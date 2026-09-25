package main

import (
	"bufio"
	"bytes"
	"errors"
	"fmt"
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

// chunk frames body in chunked transfer coding, cut at the given sizes with the
// remainder as a last data chunk. The first chunk carries an extension and every
// size is upper-case hex, so both have to be framing to the reader and not content.
func chunk(body []byte, cuts ...int) string {
	var b strings.Builder
	for i, n := range append(cuts, len(body)) {
		if n > len(body) {
			n = len(body)
		}
		if n == 0 {
			continue
		}
		ext := ""
		if i == 0 {
			ext = ";name=value"
		}
		fmt.Fprintf(&b, "%X%s\r\n%s\r\n", n, ext, body[:n])
		body = body[n:]
	}
	b.WriteString("0\r\n\r\n")
	return b.String()
}

const chunkedHead = "POST /octets HTTP/1.1\r\nHost: origin\r\nTransfer-Encoding: chunked\r\n\r\n"

// Task 4.2's octet property, sent chunked. Every octet value and a lone 0x80,
// cut into chunks of 1, 16 and 100 octets and a remainder: the recorded digest is
// the digest of those octets and nothing else, so no chunk-size line, extension
// or delimiter entered the body -- and the exchange says it arrived chunked,
// because a reader of the recording cannot otherwise tell a de-framed body from
// one that was sent as it stands.
func TestAChunkedBodyIsRecordedDeframed(t *testing.T) {
	t.Parallel()
	sent := recorder.AllOctets()
	framed := chunk(sent, 1, 16, 100)
	response, rec := exchange(t, chunkedHead+framed, reply{stated: -1})

	if !strings.HasPrefix(response, "HTTP/1.1 204 ") {
		t.Fatalf("a well-framed chunked body was answered %q", firstLine(response))
	}
	got := rec.Exchanges()
	if len(got) != 1 {
		t.Fatalf("recorded %d exchange(s), want 1", len(got))
	}
	e := got[0]
	if e.Digest != recorder.Digest(sent) || e.Length != len(sent) {
		t.Errorf("recorded %d octet(s) with digest %s; sent %d with digest %s -- chunk "+
			"framing entered the body, or content left it", e.Length, e.Digest, len(sent),
			recorder.Digest(sent))
	}
	if e.Digest == recorder.Digest([]byte(framed)) {
		t.Error("the recorded digest is the digest of the chunk-framed octets")
	}
	if !e.Chunked {
		t.Error("the exchange does not say its body arrived chunked")
	}
	if n := len(e.Fields); n != 2 || e.Fields[1] != (recorder.Field{Name: "Transfer-Encoding", Value: "chunked"}) {
		t.Errorf("the field section was not recorded as it arrived: %v", e.Fields)
	}
}

// The two framings still refused, each answered with its own refusal and neither
// recorded. Replaces the test that refused every transfer coding: a coding beside
// a length is INVALID, the second request-smuggling shape; a coding other than a
// single chunked one is framing this instrument does not IMPLEMENT.
func TestTheRefusedFramingsAreAnsweredAndNotRecorded(t *testing.T) {
	t.Parallel()
	body := chunk([]byte(fiveOctets))
	for _, c := range []struct {
		name, head, status string
	}{
		{
			name:   "a transfer coding beside a length",
			head:   "Transfer-Encoding: chunked\r\nContent-Length: 5\r\n",
			status: "400",
		},
		{
			name:   "a length beside a transfer coding",
			head:   "Content-Length: 5\r\nTransfer-Encoding: chunked\r\n",
			status: "400",
		},
		{name: "a coding other than chunked", head: "Transfer-Encoding: gzip\r\n", status: "501"},
		{name: "a list ending in chunked", head: "Transfer-Encoding: gzip, chunked\r\n", status: "501"},
		{
			name:   "chunked twice, in two fields",
			head:   "Transfer-Encoding: chunked\r\nTransfer-Encoding: chunked\r\n",
			status: "501",
		},
	} {
		t.Run(c.name, func(t *testing.T) {
			t.Parallel()
			request := "POST /refused HTTP/1.1\r\nHost: origin\r\n" + c.head + "\r\n" + body
			response, rec := exchange(t, request, reply{stated: -1})
			if got := firstLine(response); !strings.HasPrefix(got, "HTTP/1.1 "+c.status+" ") {
				t.Errorf("answered %q, want a %s", got, c.status)
			}
			if n := len(rec.Exchanges()); n != 0 {
				t.Errorf("recorded %d exchange(s) for a request it refused", n)
			}
		})
	}
}

// Chunk framing an instrument must refuse rather than read around. Each would
// otherwise record a body whose octet count is a guess.
func TestMalformedChunkingIsRefused(t *testing.T) {
	t.Parallel()
	chunked := []recorder.Field{{Name: "Transfer-Encoding", Value: "chunked"}}
	for _, c := range []struct {
		want       error
		name, body string
	}{
		{name: "a size that is not hex", body: "5x\r\nABCDE\r\n0\r\n\r\n", want: errInvalidFraming},
		{name: "a signed size", body: "-5\r\nABCDE\r\n0\r\n\r\n", want: errInvalidFraming},
		{name: "an empty size", body: "\r\nABCDE\r\n0\r\n\r\n", want: errInvalidFraming},
		{name: "data longer than its size", body: "3\r\nABCDE\r\n0\r\n\r\n", want: errInvalidFraming},
		{name: "a trailer field", body: "5\r\nABCDE\r\n0\r\nDigest: x\r\n\r\n", want: errUnimplemented},
		{name: "a body cut inside a chunk", body: "5\r\nAB", want: io.ErrUnexpectedEOF},
		{name: "a body cut before the last chunk", body: "5\r\nABCDE\r\n", want: io.ErrUnexpectedEOF},
	} {
		t.Run(c.name, func(t *testing.T) {
			t.Parallel()
			got, _, err := readBody(bufio.NewReader(strings.NewReader(c.body)), chunked)
			if !errors.Is(err, c.want) {
				t.Fatalf("read %q with error %v, want %v", got, err, c.want)
			}
			if errors.Is(err, io.EOF) {
				t.Errorf("reported %v, which run() suppresses as a quiet close", err)
			}
		})
	}
}

// The two response modes task 13.3's origin backend does not provide, and the
// default beside them. Each is asserted on the octets the origin writes and on
// the close, because a truncation is only a truncation if the connection ends.
func TestEachReplyModeWritesWhatItStates(t *testing.T) {
	t.Parallel()
	const get = "GET /reply HTTP/1.1\r\nHost: origin\r\n\r\n"
	for _, c := range []struct {
		name, status, length string
		body                 []byte
		answer               reply
	}{
		{
			name:   "a declared length closed after fewer octets",
			answer: reply{stated: 10, sent: 4},
			status: "200", length: "10", body: recorder.Pattern(10)[:4],
		},
		{
			name:   "a zero-length body on a status permitting one",
			answer: reply{stated: 0, sent: 0},
			status: "200", length: "0", body: nil,
		},
		{
			name:   "the default, which states no length on its 204",
			answer: reply{stated: -1},
			status: "204", length: "", body: nil,
		},
	} {
		t.Run(c.name, func(t *testing.T) {
			t.Parallel()
			response, _ := exchange(t, get, c.answer)
			head, body, found := strings.Cut(response, "\r\n\r\n")
			if !found {
				t.Fatalf("no end of head in %q", response)
			}
			if got := firstLine(head); !strings.HasPrefix(got, "HTTP/1.1 "+c.status+" ") {
				t.Errorf("answered %q, want a %s", got, c.status)
			}
			if got := fieldValue(head, contentLength); got != c.length {
				t.Errorf("Content-Length is %q, want %q", got, c.length)
			}
			if !bytes.Equal([]byte(body), c.body) {
				t.Errorf("wrote %d body octet(s) before the close, want %d", len(body), len(c.body))
			}
		})
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
	} {
		if _, err := newReply(c.emit, c.closeAfter, c.empty); err == nil {
			t.Errorf("%s: accepted", c.name)
		}
	}
}

func firstLine(s string) string {
	line, _, _ := strings.Cut(s, "\r\n")
	return line
}

// fieldValue is the value of the one field named name in head, or "" when there
// is none. Two would be a finding, and a test reading them would pick one.
func fieldValue(head, name string) string {
	value := ""
	for _, line := range strings.Split(head, "\r\n")[1:] {
		if n, v, ok := strings.Cut(line, ":"); ok && strings.EqualFold(n, name) {
			value = strings.TrimSpace(v)
		}
	}
	return value
}
