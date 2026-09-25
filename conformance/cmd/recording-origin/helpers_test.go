package main

// Helpers shared by the framing tests and the reply tests. They sit in their own
// file because each of those files is split along what it tests, and a helper
// both use belongs to neither.

import (
	"errors"
	"io"
	"net"
	"strings"
	"testing"

	"plugboard/conformance/recorder"
)

// exchange drives serve over an in-memory connection: it writes request, reads
// everything the origin writes before it closes, and returns that with the
// recorder serve recorded into.
//
// The write runs beside the read because net.Pipe is unbuffered, and a refusal
// stops reading before the request is through. A write the close interrupts is
// therefore expected, and only a different write error is a finding.
func exchange(t *testing.T, request string, answer reply) (string, *recorder.Ordered) {
	t.Helper()
	client, server := net.Pipe()
	rec := recorder.NewOrdered()
	served := make(chan error, 1)
	wrote := make(chan error, 1)
	go func() { served <- serve(server, rec, "", answer) }()
	go func() {
		_, err := io.WriteString(client, request)
		wrote <- err
	}()
	response, err := io.ReadAll(client)
	if err != nil {
		t.Fatalf("reading the origin's response: %v", err)
	}
	if err := <-wrote; err != nil && !errors.Is(err, io.ErrClosedPipe) {
		t.Fatalf("writing the request: %v", err)
	}
	<-served
	if err := client.Close(); err != nil {
		t.Fatalf("closing the client end: %v", err)
	}
	return string(response), rec
}

func firstLine(s string) string {
	line, _, _ := strings.Cut(s, "\r\n")
	return line
}
