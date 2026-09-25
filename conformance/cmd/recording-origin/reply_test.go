package main

// The replies the origin can be told to give, beside reply.go. Split from
// chunked_test.go, which tests reading a body and had come to hold these too.

import (
	"bytes"
	"slices"
	"strings"
	"testing"

	"plugboard/conformance/recorder"
)

// closeField ends every head the origin writes, because every reply is the last
// on its connection.
const closeField = "Connection: close"

// The two response modes task 13.3's origin backend does not provide, and the
// default beside them. Each is asserted on the octets the origin writes and on
// the close, because a truncation is only a truncation if the connection ends.
//
// The field section is compared whole, in order. Looking one field up by name
// read the last of any duplicates and nothing else, so a truncation head stating
// two lengths and a stray transfer coding passed, and so did a 204 carrying a
// length -- the one thing the 204 case exists to prove absent.
func TestEachReplyModeWritesWhatItStates(t *testing.T) {
	t.Parallel()
	const get = "GET /reply HTTP/1.1\r\nHost: origin\r\n\r\n"
	for _, c := range []struct {
		name, status string
		fields       []string
		body         []byte
		answer       reply
	}{
		{
			name:   "a declared length closed after fewer octets",
			answer: reply{stated: 10, sent: 4},
			status: "200", fields: []string{"Content-Length: 10", closeField},
			body: recorder.Pattern(10)[:4],
		},
		{
			name:   "a zero-length body on a status permitting one",
			answer: reply{stated: 0, sent: 0},
			status: "200", fields: []string{"Content-Length: 0", closeField}, body: nil,
		},
		{
			name:   "the default, which states no length on its 204",
			answer: reply{stated: -1},
			status: "204", fields: []string{closeField}, body: nil,
		},
	} {
		t.Run(c.name, func(t *testing.T) {
			t.Parallel()
			response, _ := exchange(t, get, c.answer)
			head, body, found := strings.Cut(response, "\r\n\r\n")
			if !found {
				t.Fatalf("no end of head in %q", response)
			}
			lines := strings.Split(head, "\r\n")
			if !strings.HasPrefix(lines[0], "HTTP/1.1 "+c.status+" ") {
				t.Errorf("answered %q, want a %s", lines[0], c.status)
			}
			if !slices.Equal(lines[1:], c.fields) {
				t.Errorf("wrote the fields %q, want exactly %q -- in that order, each once",
					lines[1:], c.fields)
			}
			if !bytes.Equal([]byte(body), c.body) {
				t.Errorf("wrote %d body octet(s) before the close, want %d", len(body), len(c.body))
			}
		})
	}
}

// The control for the refusals below, and the half tasks 37.10 and 38.3 lean on:
// they start the binary with these flags, and a newReply that read
// --close-after as nothing, or --empty-body as the default, would serve a
// complete response or a 204 while every test built its reply by hand and passed.
func TestEachFlagCombinationSelectsTheReplyItNames(t *testing.T) {
	t.Parallel()
	for _, c := range []struct {
		name             string
		want             reply
		emit, closeAfter int
		empty            bool
	}{
		{name: "no reply flags", emit: 0, closeAfter: -1, want: reply{stated: -1}},
		{name: "a stated length", emit: 10, closeAfter: -1, want: reply{stated: 10, sent: 10}},
		{name: "a truncation", emit: 10, closeAfter: 4, want: reply{stated: 10, sent: 4}},
		{name: "an empty body", emit: 0, closeAfter: -1, empty: true, want: reply{stated: 0, sent: 0}},
	} {
		got, err := newReply(c.emit, c.closeAfter, c.empty)
		if err != nil || got != c.want {
			t.Errorf("%s: newReply = %+v, %v; want %+v", c.name, got, err, c.want)
		}
	}
}

// A flag combination that would answer something other than what was asked for
// is refused at startup rather than served.
func TestAContradictoryReplyIsRefusedAtStartup(t *testing.T) {
	t.Parallel()
	for _, c := range []struct {
		name             string
		emit, closeAfter int
		empty            bool
	}{
		{name: "closing after every stated octet", emit: 4, closeAfter: 4},
		{name: "closing with nothing stated", emit: 0, closeAfter: 0},
		{name: "an empty body that states octets", emit: 4, closeAfter: -1, empty: true},
		{name: "a negative count", emit: -1, closeAfter: -1},
		{name: "a negative truncation point", emit: 10, closeAfter: -2},
	} {
		if _, err := newReply(c.emit, c.closeAfter, c.empty); err == nil {
			t.Errorf("%s: accepted", c.name)
		}
	}
}
