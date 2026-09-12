package recorder

import (
	"bytes"
	"fmt"
)

// T is the slice of *testing.T this suite needs. It is declared here rather than
// using testing.TB because testing.TB cannot be implemented outside the testing
// package -- and the whole point of this file is that the suite can be run over
// a deliberately defective recorder with the failures CAPTURED instead of fatal.
// An instrument nobody has tried to fool is an instrument nobody has checked.
type T interface {
	Errorf(format string, args ...any)
	Helper()
}

// Capture is a T that collects failures instead of failing. It is what lets a
// violating input assert that the suite REJECTED it.
type Capture struct{ Failures []string }

// Errorf records a failure.
func (c *Capture) Errorf(format string, args ...any) {
	c.Failures = append(c.Failures, fmt.Sprintf(format, args...))
}

// Helper does nothing; Capture is not a test helper stack.
func (c *Capture) Helper() {}

// Mentions reports whether any recorded failure contains substr.
func (c *Capture) Mentions(substr string) bool {
	for _, f := range c.Failures {
		if bytes.Contains([]byte(f), []byte(substr)) {
			return true
		}
	}
	return false
}

// AllOctets is a body carrying every value from 0x00 to 0xFF, then a lone 0x80 --
// a continuation byte with no lead byte, which is the shortest input that is not
// valid UTF-8. Anything that transcodes replaces it, and the digest moves.
func AllOctets() []byte {
	body := make([]byte, 0, 257)
	for i := 0; i < 256; i++ {
		body = append(body, byte(i))
	}
	return append(body, 0x80)
}

// AssertFaithful runs every property the instrument has to have. A recorder that
// passes all four can be trusted to tell an empty body from a full one, a
// repeated field from a collapsed one, and two method tokens from one.
//
// Each failure names the property in words a reader can act on, because this
// suite is run over an implementation somebody wrote and the failure is the only
// thing they will read.
func AssertFaithful(t T, r Recorder) {
	t.Helper()
	assertOctetsSurvive(t, r)
	assertRepeatedFieldsSurvive(t, r)
	assertMethodTokensStayDistinct(t, r)
	assertRawTargetStaysUndecoded(t, r)
}

func assertOctetsSurvive(t T, r Recorder) {
	t.Helper()
	body := AllOctets()
	r.Record([]byte("POST"), []byte("/octets"), nil, body)
	e := last(r)
	if e == nil {
		t.Errorf("body octets: nothing was recorded at all")
		return
	}
	if e.Length != len(body) {
		t.Errorf("body octets: recorded %d octet(s), sent %d -- something between "+
			"the wire and the record is dropping or adding bytes", e.Length, len(body))
	}
	if want := Digest(body); e.Digest != want {
		t.Errorf("body octets: recorded digest %s, sent %s -- the bytes changed in "+
			"transit, which is what a character encoding applied to a body looks like",
			e.Digest, want)
	}
	if !bytes.Equal(e.Body, body) {
		t.Errorf("body octets: the recorded body is not the body sent")
	}
}

func assertRepeatedFieldsSurvive(t T, r Recorder) {
	t.Helper()
	// Three lines of one field name whose values cannot legitimately be combined
	// into one, in three received spellings. Both properties at once: a map keeps
	// one of the three, and a canonicaliser loses the spellings.
	sent := []Field{
		{Name: "Set-Cookie", Value: "session=a; Path=/"},
		{Name: "set-cookie", Value: "csrf=b; Path=/"},
		{Name: "SET-COOKIE", Value: "tenant=c; Path=/"},
	}
	r.Record([]byte("GET"), []byte("/fields"), sent, nil)
	e := last(r)
	if e == nil {
		t.Errorf("repeated fields: nothing was recorded at all")
		return
	}
	if len(e.Fields) != len(sent) {
		t.Errorf("repeated fields: recorded %d field line(s), sent %d -- a repeated "+
			"field name is ordinary, and Set-Cookie past the first is a session a "+
			"client never receives", len(e.Fields), len(sent))
		return
	}
	for i, f := range sent {
		if e.Fields[i].Name != f.Name {
			t.Errorf("repeated fields: field %d recorded as name %q, received %q -- "+
				"the case a field arrived in is part of what arrived",
				i, e.Fields[i].Name, f.Name)
		}
		if e.Fields[i].Value != f.Value {
			t.Errorf("repeated fields: field %d recorded as value %q, received %q -- "+
				"order is part of the message", i, e.Fields[i].Value, f.Value)
		}
	}
}

func assertMethodTokensStayDistinct(t T, r Recorder) {
	t.Helper()
	tokens := [][]byte{[]byte("get"), []byte("GeT"), []byte("post"), []byte("PoSt")}
	fresh := len(r.Exchanges())
	for _, tok := range tokens {
		r.Record(tok, []byte("/method"), nil, nil)
	}
	seen := map[string]bool{}
	for _, e := range r.Exchanges()[fresh:] {
		seen[string(e.Method)] = true
	}
	if len(seen) != len(tokens) {
		t.Errorf("method tokens: %d distinct token(s) recorded from %d sent -- a "+
			"method token is opaque octets, and normalising it is how an allowlist "+
			"gets written by accident", len(seen), len(tokens))
	}
	for _, tok := range tokens {
		if !seen[string(tok)] {
			t.Errorf("method tokens: %q was not recorded as itself", tok)
		}
	}
}

func assertRawTargetStaysUndecoded(t T, r Recorder) {
	t.Helper()
	// %2F inside a path segment is not a separator, and a trailing slash makes a
	// collection URI a different URI. Both are lost by anything that "cleans" a
	// path before recording it.
	target := []byte("/tenant/a%2Fb/")
	r.Record([]byte("GET"), target, nil, nil)
	e := last(r)
	if e == nil {
		t.Errorf("raw target: nothing was recorded at all")
		return
	}
	if !bytes.Equal(e.RawTarget, target) {
		t.Errorf("raw target: recorded %q, received %q -- %%2F inside a segment is "+
			"not a separator and a trailing slash is part of the URI",
			e.RawTarget, target)
	}
}

func last(r Recorder) *Exchange {
	all := r.Exchanges()
	if len(all) == 0 {
		return nil
	}
	return &all[len(all)-1]
}
