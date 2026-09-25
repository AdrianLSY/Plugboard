package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"strings"
	"testing"

	"plugboard/conformance/recorder"
)

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

// The framings still refused, each answered with its own refusal and none
// recorded. Replaces the test that refused every transfer coding: a coding beside
// a length is INVALID, the second request-smuggling shape, and so is a coding on
// a request that is not HTTP/1.1; a coding other than a single chunked one is
// framing this instrument does not IMPLEMENT.
func TestTheRefusedFramingsAreAnsweredAndNotRecorded(t *testing.T) {
	t.Parallel()
	for _, c := range []struct {
		name, version, head, status string
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
		{
			name:    "chunked on an HTTP/1.0 request",
			version: "HTTP/1.0",
			head:    "Transfer-Encoding: chunked\r\n",
			status:  "400",
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
			version := c.version
			if version == "" {
				version = http11
			}
			assertRefused(t, version, c.head, c.status)
		})
	}
}

// The smuggling pair again, spelled so that a parser matching names exactly sees
// one framing field and a lenient parser sees both. Whitespace before the colon
// and a folded line each kept the misspelt name byte for byte, readBody's exact
// match missed it, and the request was recorded with a 204 -- its body read by
// whichever framing the misspelling left visible, or not read at all.
func TestAFramingFieldWhoseNameIsNotATokenIsRefused(t *testing.T) {
	t.Parallel()
	for _, c := range []struct{ name, head string }{
		{
			name: "a transfer coding with a space before its colon, beside a length",
			head: "Transfer-Encoding : chunked\r\nContent-Length: 5\r\n",
		},
		{
			name: "a length with a space before its colon, beside a transfer coding",
			head: "Content-Length : 5\r\nTransfer-Encoding: chunked\r\n",
		},
		{
			name: "a transfer coding folded onto the line before, beside a length",
			head: "X-Folded: a\r\n Transfer-Encoding: chunked\r\nContent-Length: 5\r\n",
		},
		{
			name: "a transfer coding with a space before its colon, alone",
			head: "Transfer-Encoding : chunked\r\n",
		},
	} {
		t.Run(c.name, func(t *testing.T) {
			t.Parallel()
			assertRefused(t, http11, c.head, "400")
		})
	}
}

// The rest of the token rule, and the two field lines that carry no name at all.
// Every case above is whitespace, so a readFields refusing SP and HTAB and
// nothing else passed the whole suite. RFC 9110 5.6.2 makes a name one or more
// tchar: a control octet or DEL inside one is a name that means what the parser
// reading it does with the octet. An empty name and a line with no colon are not
// field lines at all, and recording either would record a field nobody sent.
// Each is answered 400 -- an invalid message, not one this instrument declines.
func TestAFieldLineWithoutATokenForItsNameIsRefused(t *testing.T) {
	t.Parallel()
	for _, c := range []struct{ name, head string }{
		{name: "a control octet inside a name", head: "X\x01Y: a\r\n"},
		{name: "DEL inside a name", head: "X\x7fY: a\r\n"},
		{name: "an empty name, the line opening with its colon", head: ": a\r\n"},
		{name: "a field line with no colon", head: "nocolon\r\n"},
	} {
		t.Run(c.name, func(t *testing.T) {
			t.Parallel()
			assertRefused(t, http11, c.head, "400")
		})
	}
}

// assertRefused sends a request on version carrying head and a chunked body,
// and asserts that it is answered with status and recorded nowhere.
func assertRefused(t *testing.T, version, head, status string) {
	t.Helper()
	request := "POST /refused " + version + "\r\nHost: origin\r\n" + head + "\r\n" +
		chunk([]byte(fiveOctets))
	response, rec := exchange(t, request, reply{stated: -1})
	if got := firstLine(response); !strings.HasPrefix(got, "HTTP/1.1 "+status+" ") {
		t.Errorf("answered %q, want a %s", got, status)
	}
	if n := len(rec.Exchanges()); n != 0 {
		t.Errorf("recorded %d exchange(s) for a request it refused", n)
	}
}

func firstLine(s string) string {
	line, _, _ := strings.Cut(s, "\r\n")
	return line
}

// Chunk framing an instrument must refuse rather than read around. Each would
// otherwise record a body whose octet count is a guess.
//
// The bare line feeds and the lone CR were all read as clean framing: the chunk
// lines went through the head's reader, which takes a bare LF as a terminator
// and drops one CR before it. RFC 9112 7.1 ends every chunk line in CRLF, and
// 2.2's leniency stops at the end of the head.
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
		{name: "a bare LF after the size", body: "5\nABCDE\r\n0\r\n\r\n", want: errInvalidFraming},
		{name: "a bare LF after the data", body: "5\r\nABCDE\n0\r\n\r\n", want: errInvalidFraming},
		{name: "a bare LF after the last chunk", body: "5\r\nABCDE\r\n0\n\r\n", want: errInvalidFraming},
		{name: "a bare LF ending the body", body: "5\r\nABCDE\r\n0\r\n\n", want: errInvalidFraming},
		{name: "a CR inside a chunk extension", body: "5;a\rb\r\nABCDE\r\n0\r\n\r\n", want: errInvalidFraming},
		{name: "a trailer field", body: "5\r\nABCDE\r\n0\r\nDigest: x\r\n\r\n", want: errUnimplemented},
		{name: "a body cut inside a chunk", body: "5\r\nAB", want: io.ErrUnexpectedEOF},
		{name: "a body cut before the last chunk", body: "5\r\nABCDE\r\n", want: io.ErrUnexpectedEOF},
	} {
		t.Run(c.name, func(t *testing.T) {
			t.Parallel()
			got, _, err := readBody(bufio.NewReader(strings.NewReader(c.body)), []byte(http11), chunked)
			if !errors.Is(err, c.want) {
				t.Fatalf("read %q with error %v, want %v", got, err, c.want)
			}
			if errors.Is(err, io.EOF) {
				t.Errorf("reported %v, which run() suppresses as a quiet close", err)
			}
		})
	}
}
