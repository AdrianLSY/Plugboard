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

// refusedHead is a request head serve refuses before reading any of its body --
// a transfer coding beside a length -- so every octet sent after it is an octet
// the refusal leaves unread.
const refusedHead = "POST /refused HTTP/1.1\r\nHost: origin\r\n" +
	"Transfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n"

// serveOnTCP runs serve for one connection behind a real 127.0.0.1 listener and
// returns the client end, and a channel carrying what serve returned.
//
// The client end is closed at cleanup as well, so a test that fails while serve
// is still draining ends the drain rather than leaving it to its deadline. A
// test that closed it already is not a finding there.
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
	t.Cleanup(func() {
		if closeErr := client.Close(); closeErr != nil && !errors.Is(closeErr, net.ErrClosed) {
			t.Errorf("closing the client end: %v", closeErr)
		}
	})
	return client, served
}

// A refusal written while the request is still arriving reaches the peer whole,
// and then at once a clean end of stream, rather than a reset.
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
	request := refusedHead + string(recorder.Pattern(1<<20))
	wrote := make(chan error, 1)
	go func() {
		_, err := io.WriteString(client, request)
		wrote <- err
	}()
	start := time.Now()
	response, err := io.ReadAll(client)
	ended := time.Since(start)
	if err != nil {
		t.Fatalf("read %q and then %v -- the refusal ended in a reset, not a close", response, err)
	}
	const refusal = "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
	if string(response) != refusal {
		t.Errorf("read %q, want the whole refusal %q", response, refusal)
	}
	// The half-close, pinned by WHEN the end arrives rather than whether. Drained
	// without CloseWrite first, the refusal still arrives whole and still ends
	// cleanly -- once the drain gives up at its deadline and serve's deferred close
	// runs, because this peer is waiting to read and has not closed. Half of
	// lingerFor is the line: far past a loopback exchange, well short of the wait.
	if ended >= lingerFor/2 {
		t.Errorf("the end of stream arrived after %v, want well under the drain's %v -- "+
			"the origin drained before half-closing, so the peer waited out the drain "+
			"for an end it could have read at once", ended, lingerFor)
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

// The drain's octet bound. A peer that goes on sending after its refusal is read
// up to lingerCap octets and then cut off, while it is still sending and before
// it has closed. Without the cap the same peer is drained until the deadline,
// which is the wait this test times serve against.
//
// What it does not pin: the deadline. The only evidence of one is a drain that
// ends at lingerFor rather than never, and a test for that waits lingerFor out
// on every run.
func TestARefusedPeerStillSendingIsCutOffAtTheCap(t *testing.T) {
	t.Parallel()
	rec := recorder.NewOrdered()
	client, served := serveOnTCP(t, rec)
	// Past the cap by more than the 4 KiB bufio read before serve refused, which
	// the drain never sees and so never counts.
	request := append([]byte(refusedHead), recorder.Pattern(lingerCap+1<<20)...)
	wrote := make(chan error, 1)
	go func() {
		_, err := client.Write(request)
		wrote <- err
	}()
	select {
	case err := <-served:
		if !errors.Is(err, errInvalidFraming) {
			t.Errorf("serve returned %v, want the framing refusal", err)
		}
	case <-time.After(lingerFor / 2):
		t.Fatalf("serve was still draining %v in, with the peer past the %d-octet cap "+
			"-- the drain read on toward its deadline", lingerFor/2, lingerCap)
	}
	if n := len(rec.Exchanges()); n != 0 {
		t.Errorf("recorded %d exchange(s) for a request it refused", n)
	}
	if err := client.Close(); err != nil {
		t.Errorf("closing the client end: %v", err)
	}
	// The peer's write is reported and not asserted. The cut-off is a close with
	// octets unread, which is the reset lingerClose names as the price of its
	// bound, so the write fails -- unless the kernel's buffers took its last
	// octets first, which is a matter of their size and not of the origin.
	t.Logf("the peer's write ended with %v", <-wrote)
}
