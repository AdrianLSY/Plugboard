package e2e

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"testing"
	"time"

	"plugboard/conformance/recorder"
)

// A raw client, for the same reason the origin is a raw server: net/http
// normalises what these tests exist to measure. It also lets the request be
// wrong on purpose later, which a client library will not do.

func itoa(n int) string { return strconv.Itoa(n) }

func dial(t *testing.T, addr string) net.Conn {
	t.Helper()
	dialer := net.Dialer{Timeout: 10 * time.Second}
	conn, err := dialer.DialContext(t.Context(), "tcp", addr)
	if err != nil {
		t.Fatalf("dialling the client edge at %s: %v", addr, err)
	}
	return conn
}

// postAndRead sends body and returns what the origin recorded for it. recordDir
// is the directory the origin was told to write into -- passed in rather than
// recreated here, because a helper that invented its own directory would find no
// recordings and report that as "the origin recorded nothing".
func postAndRead(t *testing.T, addr string, recordDir string, body []byte) recorder.Exchange {
	t.Helper()
	conn := dial(t, addr)
	defer func() {
		if err := conn.Close(); err != nil {
			t.Logf("closing the client connection: %v", err)
		}
	}()

	head := fmt.Sprintf("POST /octets HTTP/1.1\r\nHost: edge\r\nContent-Length: %d\r\n\r\n",
		len(body))
	if _, err := conn.Write(append([]byte(head), body...)); err != nil {
		t.Fatalf("sending %d octet(s): %v", len(body), err)
	}
	if _, err := io.Copy(io.Discard, conn); err != nil {
		t.Fatalf("reading the response: %v", err)
	}
	return lastRecording(t, recordDir)
}

// getAndRead returns the response body octets the client actually received.
func getAndRead(t *testing.T, addr string) []byte {
	t.Helper()
	conn := dial(t, addr)
	defer func() {
		if err := conn.Close(); err != nil {
			t.Logf("closing the client connection: %v", err)
		}
	}()

	if _, err := conn.Write([]byte("GET /octets HTTP/1.1\r\nHost: edge\r\n\r\n")); err != nil {
		t.Fatalf("sending the request: %v", err)
	}
	br := bufio.NewReader(conn)
	for {
		line, err := br.ReadBytes('\n')
		if err != nil {
			t.Fatalf("reading the response head: %v", err)
		}
		if len(bytes.TrimRight(line, "\r\n")) == 0 {
			break
		}
	}
	body, err := io.ReadAll(br) // not-a-wire-payload: this IS the assertion; the client is the far end
	if err != nil {
		t.Fatalf("reading the response body: %v", err)
	}
	return body
}

// lastRecording reads what the origin wrote, rather than asking the origin.
func lastRecording(t *testing.T, dir string) recorder.Exchange {
	t.Helper()
	names, err := filepath.Glob(filepath.Join(dir, "exchange-*.json"))
	if err != nil || len(names) == 0 {
		t.Fatalf("the origin recorded nothing in %s", dir)
	}
	blob, err := os.ReadFile(names[len(names)-1])
	if err != nil {
		t.Fatalf("reading the recording: %v", err)
	}
	var e struct {
		Digest string `json:"digest_sha256"`
		Length int    `json:"octet_count"`
	}
	if err := json.Unmarshal(blob, &e); err != nil {
		t.Fatalf("parsing the recording: %v", err)
	}
	return recorder.Exchange{Digest: e.Digest, Length: e.Length}
}
