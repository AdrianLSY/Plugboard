package main

import (
	"bufio"
	"strings"
	"testing"

	"plugboard/conformance/recorder"
)

// The framing an instrument refuses to guess at.
//
// This file exists because the instrument guessed. `Content-Length: 5` followed
// by `Content-Length: 3` was read as 3 -- the loop assigned over its own result,
// so the LAST field won silently -- and `Content-Length: -5` parsed, went
// negative, and fell through the `length <= 0` branch as though no body had been
// declared. Both answered 204 and recorded an exchange, which is the one outcome
// worse than refusing: a recorded measurement that is wrong rather than absent.
//
// Two Content-Length fields is not a curiosity. It is one of the two canonical
// request-smuggling shapes, and the other one -- Content-Length beside
// Transfer-Encoding -- this instrument already refused. D6 makes framing per-hop
// and never relayed, so a correct proxy generates its own and the origin never
// sees a duplicate; seeing one means the hop under measurement is broken, which
// is precisely when an instrument must stop rather than pick a winner.
//
// RFC 9112 6.3 makes an invalid Content-Length an unrecoverable framing error a
// server answers with 400 and a close. It permits collapsing *identical*
// duplicates instead of rejecting them; this instrument rejects them, because
// collapsing is normalising and the package this lives in is documented as
// normalising nothing.
func TestMalformedFramingIsRefusedRatherThanGuessedAt(t *testing.T) {
	t.Parallel()
	for _, c := range []struct {
		name     string
		fields   []recorder.Field
		body     string
		mentions string
	}{
		{
			name:     "two lengths that disagree",
			fields:   []recorder.Field{{Name: "Content-Length", Value: "5"}, {Name: "Content-Length", Value: "3"}},
			body:     "ABCDE",
			mentions: "more than one",
		},
		{
			name:     "two lengths that agree",
			fields:   []recorder.Field{{Name: "Content-Length", Value: "5"}, {Name: "content-length", Value: "5"}},
			body:     "ABCDE",
			mentions: "more than one",
		},
		{
			name:     "one field carrying a list",
			fields:   []recorder.Field{{Name: "Content-Length", Value: "5, 5"}},
			body:     "ABCDE",
			mentions: "not a count",
		},
		{
			name:     "a negative length",
			fields:   []recorder.Field{{Name: "Content-Length", Value: "-5"}},
			mentions: "not a count",
		},
		{
			name:     "a signed length",
			fields:   []recorder.Field{{Name: "Content-Length", Value: "+5"}},
			body:     "ABCDE",
			mentions: "not a count",
		},
		{
			name:     "a length that is not a number at all",
			fields:   []recorder.Field{{Name: "Content-Length", Value: "five"}},
			mentions: "not a count",
		},
	} {
		t.Run(c.name, func(t *testing.T) {
			t.Parallel()
			got, err := readBody(bufio.NewReader(strings.NewReader(c.body)), c.fields)
			if err == nil {
				t.Fatalf("read %d octet(s) and reported no error -- the instrument "+
					"resolved a framing ambiguity instead of refusing it, so an "+
					"exchange was recorded whose octet count is a guess", len(got))
			}
			if !strings.Contains(err.Error(), c.mentions) {
				t.Errorf("the refusal does not say what was wrong: want it to mention "+
					"%q, got %q", c.mentions, err)
			}
		})
	}
}

// The control. An instrument that refused everything would pass the cases above
// and measure nothing, so the two shapes that ARE valid are asserted here.
func TestWellFramedBodiesAreStillRead(t *testing.T) {
	t.Parallel()
	t.Run("a declared length reads exactly that many octets", func(t *testing.T) {
		t.Parallel()
		body, err := readBody(bufio.NewReader(strings.NewReader("ABCDEtrailing")),
			[]recorder.Field{{Name: "Content-Length", Value: "5"}})
		if err != nil {
			t.Fatalf("a single valid Content-Length was refused: %v", err)
		}
		if string(body) != "ABCDE" {
			t.Errorf("read %q, want %q", body, "ABCDE")
		}
	})
	t.Run("no length field means no body", func(t *testing.T) {
		t.Parallel()
		body, err := readBody(bufio.NewReader(strings.NewReader("")),
			[]recorder.Field{{Name: "Host", Value: "x"}})
		if err != nil {
			t.Fatalf("a request with no body was refused: %v", err)
		}
		if len(body) != 0 {
			t.Errorf("read %d octet(s) from a request declaring no body", len(body))
		}
	})
}

// The refusal this instrument already had, asserted so the fix above cannot
// quietly reclassify it. A transfer coding is framing this instrument does not
// IMPLEMENT; a malformed length is framing that is INVALID. They are different
// answers to the sender and the distinction is worth keeping.
func TestATransferCodingIsStillRefusedAsUnimplemented(t *testing.T) {
	t.Parallel()
	_, err := readBody(bufio.NewReader(strings.NewReader("")),
		[]recorder.Field{{Name: "Transfer-Encoding", Value: "chunked"}})
	if err == nil {
		t.Fatal("a chunked body was accepted; this instrument reads Content-Length framing only")
	}
	if !strings.Contains(err.Error(), "transfer-encoding") {
		t.Errorf("the refusal does not name the coding it will not read: %v", err)
	}
}
