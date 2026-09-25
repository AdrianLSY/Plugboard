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
// It reads two framings: a declared Content-Length, and a single chunked
// transfer coding, whose chunk framing it removes and records that it removed.
// Any other framing is refused loudly with a stated reason rather than read
// wrongly, because an instrument that guesses is worse than one that stops.
//
// It answers in one of four ways, chosen at startup: 204 with no content, which
// is the default; 200 with a stated number of recorder.Pattern octets; the same
// head with the connection closed after fewer octets than it stated, which is the
// truncation a proxy must not report as a complete response; and 200 stating a
// length of zero, which is the empty body on a status that permits one.
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
	"strings"
	"time"

	"plugboard/conformance/internal/buildstamp"

	"plugboard/conformance/recorder"
)

func main() {
	listen := flag.String("listen", "127.0.0.1:0", "address to listen on")
	recordDir := flag.String("record-dir", "", "directory to write one file per exchange into")
	readyFile := flag.String("ready-file", "", "file to write the bound address into once listening")
	emitBytes := flag.Int("emit-bytes", 0, "respond 200 stating and sending this many octets of recorder.Pattern")
	closeAfter := flag.Int("close-after", -1, "with --emit-bytes, close after sending this many of the octets it stated")
	emptyBody := flag.Bool("empty-body", false, "respond 200 stating a length of zero")
	flag.Parse()

	if _, err := fmt.Fprintln(os.Stdout, buildstamp.Line()); err != nil {
		os.Exit(1)
	}
	answer, err := newReply(*emitBytes, *closeAfter, *emptyBody)
	if err == nil {
		err = run(*listen, *recordDir, *readyFile, answer)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "recording-origin: %v\n", err)
		os.Exit(1)
	}
}

func run(listen, recordDir, readyFile string, answer reply) error {
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
		// Inline, one connection at a time. lingerClose says what that costs.
		if err := serve(conn, rec, recordDir, answer); err != nil &&
			!errors.Is(err, io.EOF) {
			warn(err)
		}
	}
}

func serve(conn net.Conn, rec *recorder.Ordered, recordDir string, answer reply) error {
	defer closing(conn, "connection")
	br := bufio.NewReader(conn)

	method, target, version, err := readRequestLine(br)
	if err != nil {
		return err
	}
	fields, err := readFields(br)
	if err != nil {
		return refuse(conn, err)
	}
	body, chunked, err := readBody(br, version, fields)
	if err != nil {
		return refuse(conn, err)
	}

	if chunked {
		rec.RecordChunked(method, target, fields, body)
	} else {
		rec.Record(method, target, fields, body)
	}
	if recordDir != "" {
		if err := recorder.Persist(recordDir, rec.Exchanges()); err != nil {
			return err
		}
	}
	return writeReply(conn, answer)
}

// refuse answers a request this instrument will not record, and returns err.
//
// 400 for framing that is INVALID, 501 for framing this instrument does not
// implement. RFC 9112 6.3 makes an invalid Content-Length an unrecoverable error
// answered with 400; a transfer coding other than chunked is a thing this origin
// declines to read, which is a different statement. Anything else -- a body that
// stopped early -- is not a refusal the peer can act on, and gets no answer.
//
// One switch serves the field section and the body alike. The field-name
// refusal arrived after this switch, and returning its error bare would have
// closed the connection with no answer: refused, but silently, which a peer
// cannot tell from a crash.
func refuse(conn net.Conn, err error) error {
	var status string
	switch {
	case errors.Is(err, errInvalidFraming):
		status = "400 Bad Request"
	case errors.Is(err, errUnimplemented):
		status = "501 Not Implemented"
	default:
		return err
	}
	if writeErr := writeStatus(conn, status, nil); writeErr != nil {
		warn(writeErr)
		return err
	}
	lingerClose(conn)
	return err
}

// The bounds on a lingering close: long enough for a peer to finish sending what
// it had already written when the refusal reached it, and few enough octets that
// a peer sending without end is cut off rather than read without end.
const (
	lingerFor = 2 * time.Second
	lingerCap = 8 << 20
)

// lingerClose is RFC 9112 9.6's lingering close, after a refusal.
//
// A refusal is written while the rest of the request may still be arriving -- a
// body past bufio's first 4 KiB, or the tail after a malformed chunk. A TCP stack
// closed with octets unread in its receive buffer answers with a reset rather
// than a FIN, and the peer then reads `connection reset by peer`, often before
// the refusal it was sent: a transport failure where this instrument stated a
// reason. So the write side is closed first, which delivers the refusal and its
// end, and what the peer still sends is read and discarded -- bounded in time and
// in octets, because the peer chooses how much it sends and this instrument is
// pointed at adversarial inputs by design.
//
// What it does not decide: a peer still sending past the cap is reset when
// serve's deferred close runs. That is the price of a bound, and a peer sending
// megabytes after its refusal arrived has stopped listening for one.
//
// Nor does it keep one peer from holding up the next. run() serves every
// connection inline in its accept loop, so a peer that keeps a refused
// connection open delays the next accept by up to lingerFor -- and a proxy
// under test that holds its refused connections open adds that much to every
// exchange queued behind each one. That is the price of a sequential recorder:
// serving one connection at a time is what numbers the persisted exchanges in
// the order they were served, and what lets recorder.Ordered, which takes no
// lock, be written from one goroutine only.
func lingerClose(conn net.Conn) {
	// TCP only. The reset this prevents is a TCP stack's answer to a close with
	// unread octets; net.Pipe, which the unit tests serve over, has no receive
	// buffer, sends no reset and cannot half-close, so draining one would do
	// nothing but wait out the deadline before the test's reader saw the close.
	tcp, ok := conn.(*net.TCPConn)
	if !ok {
		return
	}
	if err := tcp.CloseWrite(); err != nil {
		warn(fmt.Errorf("half-closing after a refusal: %w", err))
		return
	}
	if err := tcp.SetReadDeadline(time.Now().Add(lingerFor)); err != nil {
		warn(fmt.Errorf("bounding the drain after a refusal: %w", err))
		return
	}
	// The drain ends at the peer's close, at the cap or at the deadline. The
	// last two are the bound working rather than a finding: the cap ends the
	// copy with no error at all, and the deadline is the one error kept quiet.
	if _, err := io.Copy(io.Discard, io.LimitReader(tcp, lingerCap)); err != nil &&
		!errors.Is(err, os.ErrDeadlineExceeded) {
		warn(fmt.Errorf("draining a refused request: %w", err))
	}
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

// readRequestLine returns the version token too, because RFC 9112 6.1 makes a
// transfer coding on a request that is not HTTP/1.1 faulty framing, and only the
// version says which requests those are. It is not recorded: the persisted
// format is what later assertions read, and none of them asks for it.
func readRequestLine(br *bufio.Reader) (method, target, version []byte, err error) {
	line, err := readLine(br)
	if err != nil {
		return nil, nil, nil, err
	}
	first := bytes.IndexByte(line, ' ')
	last := bytes.LastIndexByte(line, ' ')
	if first < 0 || last <= first {
		return nil, nil, nil, fmt.Errorf("malformed request line: %q", line)
	}
	return line[:first], line[first+1 : last], line[last+1:], nil
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
			return nil, fmt.Errorf("%w: field line %q has no colon", errInvalidFraming, line)
		}
		// The name must be a token, RFC 9110 5.6.2, and nothing wider. Whitespace
		// before the colon, a line folded onto the one before it (obs-fold, which
		// opens with a space or a tab) and a control octet each make a name that
		// hops read differently: `Transfer-Encoding : chunked` is a transfer
		// coding to one parser and an unknown field to another, and beside a
		// Content-Length that disagreement is request smuggling -- readBody's
		// refusal of the pair never fired, because it matches names exactly.
		// RFC 9112 5.1 requires the 400 for whitespace before the colon and 5.2
		// permits it for obs-fold; every other non-token is refused alike rather
		// than recorded as a name whose meaning depends on who reads it.
		if !isToken(line[:colon]) {
			return nil, fmt.Errorf("%w: field name %q is not a token -- whitespace before "+
				"the colon, an obs-fold line or a control octet", errInvalidFraming, line[:colon])
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

// isToken reports whether name is one or more tchar, RFC 9110 5.6.2.
func isToken(name []byte) bool {
	for _, c := range name {
		alnum := 'a' <= c && c <= 'z' || 'A' <= c && c <= 'Z' || '0' <= c && c <= '9'
		if !alnum && strings.IndexByte("!#$%&'*+-.^_`|~", c) < 0 {
			return false
		}
	}
	return len(name) > 0
}

// readLine reads one line of the request head, where RFC 9112 2.2 lets a
// recipient take a bare LF as the terminator. That permission covers the start
// line and the field lines and nothing after them; see readFramingLine.
func readLine(br *bufio.Reader) ([]byte, error) {
	line, err := br.ReadBytes('\n')
	if err != nil {
		return nil, err
	}
	return bytes.TrimSuffix(bytes.TrimSuffix(line, []byte("\n")), []byte("\r")), nil
}
