// Command recording-origin is the instrument at the far end of the harness: an
// origin that records what actually arrived and never decodes, validates or
// transcodes an octet.
//
// It reads HTTP/1.1 off the socket itself rather than using net/http, and that
// is not reinvention. net/http canonicalises every field name through
// textproto.CanonicalMIMEHeaderKey and hands the section over as a map -- so the
// case a field arrived in is gone before any assertion can see it, and the two
// properties this instrument exists to measure are the two it would have lost.
//
// What it deliberately does not do: chunked transfer coding. A body whose
// framing it cannot read is refused loudly with a stated reason rather than read
// wrongly, because an instrument that guesses is worse than one that stops.
package main

import (
	"bufio"
	"bytes"
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"os"
	"strconv"
	"strings"

	"plugboard/conformance/recorder"
)

func main() {
	listen := flag.String("listen", "127.0.0.1:0", "address to listen on")
	recordDir := flag.String("record-dir", "", "directory to write one file per exchange into")
	readyFile := flag.String("ready-file", "", "file to write the bound address into once listening")
	emitBytes := flag.Int("emit-bytes", 0, "respond with this many octets of recorder.Pattern")
	flag.Parse()

	if err := run(*listen, *recordDir, *readyFile, *emitBytes); err != nil {
		fmt.Fprintf(os.Stderr, "recording-origin: %v\n", err)
		os.Exit(1)
	}
}

func run(listen, recordDir, readyFile string, emitBytes int) error {
	var lc net.ListenConfig
	ln, err := lc.Listen(context.Background(), "tcp", listen)
	if err != nil {
		return fmt.Errorf("listening on %s: %w", listen, err)
	}
	defer closing(ln, "listener")

	// The readiness surface. The harness waits on THIS and on nothing else --
	// never on a sleep, which is how a harness comes to hide a process that
	// never started.
	if readyFile != "" {
		if err := os.WriteFile(readyFile, []byte(ln.Addr().String()+"\n"), 0o600); err != nil {
			return fmt.Errorf("writing the readiness file: %w", err)
		}
	}
	if _, err := fmt.Fprintf(os.Stdout, "listening %s\n", ln.Addr().String()); err != nil {
		return fmt.Errorf("announcing the bound address: %w", err)
	}

	rec := recorder.NewOrdered()
	for {
		conn, err := ln.Accept()
		if err != nil {
			return nil
		}
		if err := serve(conn, rec, recordDir, emitBytes); err != nil &&
			!errors.Is(err, io.EOF) {
			warn(err)
		}
	}
}

func serve(conn net.Conn, rec *recorder.Ordered, recordDir string, emitBytes int) error {
	defer closing(conn, "connection")
	br := bufio.NewReader(conn)

	method, target, err := readRequestLine(br)
	if err != nil {
		return err
	}
	fields, err := readFields(br)
	if err != nil {
		return err
	}
	body, err := readBody(br, fields)
	if err != nil {
		if writeErr := writeStatus(conn, "501 Not Implemented", nil); writeErr != nil {
			warn(writeErr)
		}
		return err
	}

	rec.Record(method, target, fields, body)
	if recordDir != "" {
		if err := recorder.Persist(recordDir, rec.Exchanges()); err != nil {
			return err
		}
	}
	if emitBytes > 0 {
		return writeStatus(conn, "200 OK", recorder.Pattern(emitBytes))
	}
	return writeStatus(conn, "204 No Content", nil)
}

// closing reports what it could not close instead of discarding it. `_ =` is not
// available: errcheck runs with check-blank, because an error assigned to blank
// is an error somebody decided not to read.
func closing(c io.Closer, what string) {
	if err := c.Close(); err != nil {
		warn(fmt.Errorf("closing the %s: %w", what, err))
	}
}

func warn(err error) {
	if _, writeErr := fmt.Fprintf(os.Stderr, "recording-origin: %v\n", err); writeErr != nil {
		panic(writeErr)
	}
}

func readRequestLine(br *bufio.Reader) (method, target []byte, err error) {
	line, err := readLine(br)
	if err != nil {
		return nil, nil, err
	}
	first := bytes.IndexByte(line, ' ')
	last := bytes.LastIndexByte(line, ' ')
	if first < 0 || last <= first {
		return nil, nil, fmt.Errorf("malformed request line: %q", line)
	}
	return line[:first], line[first+1 : last], nil
}

func readFields(br *bufio.Reader) ([]recorder.Field, error) {
	var fields []recorder.Field
	for {
		line, err := readLine(br)
		if err != nil {
			return nil, err
		}
		if len(line) == 0 {
			return fields, nil
		}
		colon := bytes.IndexByte(line, ':')
		if colon < 0 {
			return nil, fmt.Errorf("malformed field line: %q", line)
		}
		// The NAME is kept byte for byte, in the case it arrived in. Only
		// surrounding whitespace is stripped from the value, which RFC 9110
		// makes not part of it.
		fields = append(fields, recorder.Field{
			Name:  string(line[:colon]),
			Value: strings.Trim(string(line[colon+1:]), " \t"),
		})
	}
}

func readBody(br *bufio.Reader, fields []recorder.Field) ([]byte, error) {
	length := -1
	for _, f := range fields {
		switch strings.ToLower(f.Name) {
		case "transfer-encoding":
			return nil, fmt.Errorf("transfer-encoding %q: this instrument reads "+
				"Content-Length framing only, and refuses rather than guessing at a "+
				"body it cannot frame", f.Value)
		case "content-length":
			n, err := strconv.Atoi(f.Value)
			if err != nil {
				return nil, fmt.Errorf("content-length %q: %w", f.Value, err)
			}
			length = n
		}
	}
	if length <= 0 {
		return nil, nil
	}
	body := make([]byte, length)
	if _, err := io.ReadFull(br, body); err != nil {
		return nil, fmt.Errorf("reading %d body octet(s): %w", length, err)
	}
	return body, nil
}

func readLine(br *bufio.Reader) ([]byte, error) {
	line, err := br.ReadBytes('\n')
	if err != nil {
		return nil, err
	}
	return bytes.TrimSuffix(bytes.TrimSuffix(line, []byte("\n")), []byte("\r")), nil
}

func writeStatus(w io.Writer, status string, body []byte) error {
	head := fmt.Sprintf("HTTP/1.1 %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n",
		status, len(body))
	if _, err := w.Write([]byte(head)); err != nil {
		return fmt.Errorf("writing the status line: %w", err)
	}
	if len(body) > 0 {
		if _, err := w.Write(body); err != nil {
			return fmt.Errorf("writing %d body octet(s): %w", len(body), err)
		}
	}
	return nil
}
