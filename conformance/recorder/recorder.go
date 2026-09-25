// Package recorder is the instrument. It records what a request actually
// carried, and it is proven to discriminate before anything is measured with it.
//
// Nothing here decodes, validates or transcodes an octet. That is the whole
// design: the prior attempt's suite could not tell an empty body from a full
// one, because every path between the wire and the assertion had already
// normalised what it was carrying. An instrument that normalises is an
// instrument that agrees with whatever it is pointed at.
//
// Three type choices carry that, and each is the inverse of a prior-art defect:
//
//   - A field section is an ORDERED SLICE of pairs, never a map. A repeated name
//     is ordinary and the order is part of the message; `Set-Cookie` is the case
//     that proves it, and the prior attempt deleted every one past the first with
//     no error and no log line.
//   - A method token is OPAQUE OCTETS, never a normalised string. Four tokens
//     differing only in case are four tokens.
//   - A body is octets and a digest over those octets, never a string. No
//     character encoding is applied at any point.
package recorder

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Field is one field line exactly as it arrived: the name in the case it was
// received in, and the value with at most one leading space removed.
type Field struct {
	Name  string
	Value string
}

// Exchange is what one request left behind.
//
// Field order is chosen for govet's fieldalignment, which is on because task 2.3
// asked for `enable-all` and the trade was accepted rather than tuned away. It
// reads fine anyway: the digest is the identity of what arrived.
//
// Chunked says the body arrived in chunked transfer coding and Body holds the
// octets with the chunk framing removed -- sizes, extensions and delimiters are
// framing, not content, and a digest over them would measure the hop's framing
// rather than what was sent through it.
type Exchange struct {
	Digest    string
	Method    []byte
	RawTarget []byte
	Fields    []Field
	Body      []byte
	Length    int
	Chunked   bool
}

// Recorder is the interface the assertion suite is written against, so the same
// suite can be run over a deliberately defective implementation and shown to
// reject it. See AssertFaithful.
type Recorder interface {
	Record(method, rawTarget []byte, fields []Field, body []byte)
	Exchanges() []Exchange
}

// Ordered is the faithful recorder. It appends; it never keys.
type Ordered struct {
	exchanges []Exchange
}

// NewOrdered returns a recorder that preserves order, repetition and case.
func NewOrdered() *Ordered { return &Ordered{} }

// Record stores one exchange verbatim. Every slice is copied, because the caller
// owns its buffers and a recorder that aliased them would report whatever the
// caller did next.
func (o *Ordered) Record(method, rawTarget []byte, fields []Field, body []byte) {
	o.record(method, rawTarget, fields, body, false)
}

// RecordChunked stores one exchange whose body arrived in chunked transfer
// coding, body being the de-framed octets. It is not on the Recorder interface:
// the assertion suite measures fidelity, which framing does not change, and the
// deliberately defective recorder it is proven against should differ from this
// one in exactly the two properties it was built to get wrong.
func (o *Ordered) RecordChunked(method, rawTarget []byte, fields []Field, body []byte) {
	o.record(method, rawTarget, fields, body, true)
}

func (o *Ordered) record(method, rawTarget []byte, fields []Field, body []byte, chunked bool) {
	sum := sha256.Sum256(body)
	o.exchanges = append(o.exchanges, Exchange{
		Method:    append([]byte(nil), method...),
		RawTarget: append([]byte(nil), rawTarget...),
		Fields:    append([]Field(nil), fields...),
		Body:      append([]byte(nil), body...),
		Digest:    hex.EncodeToString(sum[:]),
		Length:    len(body),
		Chunked:   chunked,
	})
}

// Exchanges returns the exchanges in the order they were recorded.
func (o *Ordered) Exchanges() []Exchange { return o.exchanges }

// persisted is the on-disk shape. Octets are base64 rather than strings: a JSON
// string would apply a character encoding to a body, which is the defect class
// this instrument exists to detect.
type persisted struct {
	Method    string      `json:"method_b64"`
	RawTarget string      `json:"raw_target_b64"`
	Body      string      `json:"body_b64"`
	Digest    string      `json:"digest_sha256"`
	Fields    [][2]string `json:"fields"`
	Length    int         `json:"octet_count"`
	Chunked   bool        `json:"chunked"`
}

// Persist writes one file per exchange into dir, named by its index.
func Persist(dir string, exchanges []Exchange) error {
	if err := os.MkdirAll(dir, 0o750); err != nil {
		return fmt.Errorf("recording directory: %w", err)
	}
	for i, e := range exchanges {
		fields := make([][2]string, 0, len(e.Fields))
		for _, f := range e.Fields {
			fields = append(fields, [2]string{f.Name, f.Value})
		}
		blob, err := json.MarshalIndent(persisted{
			Method:    base64.StdEncoding.EncodeToString(e.Method),
			RawTarget: base64.StdEncoding.EncodeToString(e.RawTarget),
			Fields:    fields,
			Body:      base64.StdEncoding.EncodeToString(e.Body),
			Digest:    e.Digest,
			Length:    e.Length,
			Chunked:   e.Chunked,
		}, "", "  ")
		if err != nil {
			return fmt.Errorf("exchange %d: %w", i, err)
		}
		name := filepath.Join(dir, fmt.Sprintf("exchange-%04d.json", i))
		if err := os.WriteFile(name, append(blob, '\n'), 0o600); err != nil {
			return fmt.Errorf("exchange %d: %w", i, err)
		}
	}
	return nil
}

// Digest is the digest of b, in the same form Exchange.Digest carries, so a
// caller can compute what it sent and compare without importing a hash package.
func Digest(b []byte) string {
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

// Pattern returns n octets covering every value from 0x00 to 0xFF and carrying a
// lone 0x80 -- a continuation byte with no lead byte, so the sequence is not
// valid UTF-8 and anything that transcodes it moves the digest. Deterministic,
// so a client and an origin can each generate it and compare without sending it
// twice.
func Pattern(n int) []byte {
	body := make([]byte, n)
	for i := range body {
		body[i] = byte(i % 256)
	}
	if n > 0 {
		body[n/2] = 0x80
	}
	return body
}
