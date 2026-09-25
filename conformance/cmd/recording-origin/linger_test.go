package main

// The refusal path over a real TCP connection, where a close with octets still
// unread is a reset. Every other test here serves over net.Pipe, which has no
// reset, so "answered with its refusal" had been shown only on a transport where
// the defect this file pins cannot happen.

import (
	"errors"
	"io"
	"net"
	"testing"
	"time"

	"plugboard/conformance/recorder"
)

// serveOnTCP runs serve for one connection behind a real 127.0.0.1 listener and
// returns the client end, and a channel carrying what serve returned.
func serveOnTCP(t *testing.T, rec *recorder.Ordered) (net.Conn, <-chan error) {
	t.Helper()
	var lc net.ListenConfig
	ln, err := lc.Listen(t.Context(), "tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listening: %v", err)
	}
	t.Cleanup(func() {
		if closeErr := ln.Close(); closeErr != nil {
			t.Errorf("closing the listener: %v", closeErr)
		}
	})
	served := make(chan error, 1)
	go func() {
		conn, acceptErr := ln.Accept()
		if acceptErr != nil {
			served <- acceptErr
			return
		}
		served <- serve(conn, rec, "", reply{stated: -1})
	}()
	var d net.Dialer
	client, err := d.DialContext(t.Context(), "tcp", ln.Addr().String())
	if err != nil {
		t.Fatalf("dialling the origin: %v", err)
	}
	return client, served
}

// A refusal written while the request is still arriving reaches the peer whole,
// and then a clean end of stream, rather than a reset.
//
// Before the lingering close, serve wrote its 400 and closed with most of the
// body unread in the kernel's receive buffer, and the TCP stack answered that
// close with a reset: the client's write failed with a broken pipe and its read
// with `connection reset by peer`, and a real client lost the refusal about half
// the time. 1 MiB because it is the size task 4.3 sends, and far past both
// bufio's 4 KiB and what loopback buffers before a writer has to wait.
func TestARefusalOverTCPEndsInACloseRatherThanAReset(t *testing.T) {
	t.Parallel()
	rec := recorder.NewOrdered()
	client, served := serveOnTCP(t, rec)
	// A bound, so a regression fails here rather than at the test binary's timeout.
	if err := client.SetDeadline(time.Now().Add(10 * time.Second)); err != nil {
		t.Fatalf("bounding the exchange: %v", err)
	}
	request := "POST /refused HTTP/1.1\r\nHost: origin\r\n" +
		"Transfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n" + string(recorder.Pattern(1<<20))
	wrote := make(chan error, 1)
	go func() {
		_, err := io.WriteString(client, request)
		wrote <- err
	}()
	response, err := io.ReadAll(client)
	if err != nil {
		t.Fatalf("read %q and then %v -- the refusal ended in a reset, not a close", response, err)
	}
	const refusal = "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
	if string(response) != refusal {
		t.Errorf("read %q, want the whole refusal %q", response, refusal)
	}
	if err := <-wrote; err != nil {
		t.Errorf("writing the request failed with %v -- the origin stopped reading "+
			"before the peer was through, and closed on what it had not read", err)
	}
	if err := client.Close(); err != nil {
		t.Errorf("closing the client end: %v", err)
	}
	if err := <-served; !errors.Is(err, errInvalidFraming) {
		t.Errorf("serve returned %v, want the framing refusal", err)
	}
	if n := len(rec.Exchanges()); n != 0 {
		t.Errorf("recorded %d exchange(s) for a request it refused", n)
	}
}
