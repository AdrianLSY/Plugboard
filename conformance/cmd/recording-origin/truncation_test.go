package main

import (
	"bufio"
	"errors"
	"io"
	"strings"
	"testing"

	"plugboard/conformance/recorder"
)

// A body that stops early is a finding, and run() decides what reaches an
// operator by asking whether the error is io.EOF -- that suppression exists so
// an ordinary connection close stays quiet.
//
// io.ReadFull said io.ErrUnexpectedEOF when a body stopped short, which is not
// io.EOF, so it was reported. io.CopyN says io.EOF for the same condition. The
// switch to CopyN, made to stop pre-allocating from a peer-supplied number,
// therefore moved the truncated-body case into the quiet branch: a request
// declaring five octets and sending two was recorded nowhere and warned about
// nowhere.
//
// This case is written against the CLASS rather than the message, because the
// class is what run() branches on. An implementation that printed a nice string
// but still returned something io.EOF-shaped would pass a substring assertion
// and stay silent in production.
func TestATruncatedBodyIsReportedRatherThanReadAsACleanClose(t *testing.T) {
	t.Parallel()
	_, err := readBody(bufio.NewReader(strings.NewReader("AB")),
		[]recorder.Field{{Name: contentLength, Value: "5"}})
	if err == nil {
		t.Fatal("a body declaring five octets and carrying two was accepted")
	}
	if errors.Is(err, io.EOF) {
		t.Errorf("a truncated body reports %v, which run() suppresses as a clean "+
			"connection close -- so the one hop that saw the truncation tells nobody. "+
			"io.ReadFull reported this as io.ErrUnexpectedEOF and it was printed", err)
	}
	if !errors.Is(err, io.ErrUnexpectedEOF) {
		t.Errorf("a truncated body reports %v; the condition is an unexpected EOF and "+
			"saying so is what keeps it out of the quiet branch", err)
	}
}

// The control. Suppressing io.EOF is deliberate: a connection that closes
// between requests is not a finding, and an instrument that warned on every one
// would bury the truncations in noise. So the quiet branch must stay quiet for
// the case it was built for.
func TestAnEmptyRequestIsStillAQuietEndRatherThanAFinding(t *testing.T) {
	t.Parallel()
	_, _, err := readRequestLine(bufio.NewReader(strings.NewReader("")))
	if err == nil {
		t.Fatal("a connection carrying no request line was read as a request")
	}
	if !errors.Is(err, io.EOF) {
		t.Errorf("a connection that closed before sending anything reports %v, which "+
			"run() prints -- an idle close is not a finding and reporting it buries "+
			"the ones that are", err)
	}
}
