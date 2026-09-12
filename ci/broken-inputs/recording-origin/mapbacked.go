// Package mapbacked is the instrument built wrong, on purpose.
//
// It makes exactly the two type choices the prior attempt made, and no others:
// a field section keyed by a canonicalised name, and a method token normalised
// to upper case. Everything else -- the body octets, the digest, the raw target
// -- is faithful, so the assertion suite is shown to reject these two properties
// specifically rather than rejecting a broken implementation generally.
package mapbacked

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"

	"plugboard/conformance/recorder"
)

// MapBacked records a field section as map[string]string and upper-cases the
// method token. `proxy_controller.ex:496` was `Enum.into(conn.req_headers, %{})`
// and `telephone.go:85` was the same shape in Go; the router at `router.ex:63-69`
// matched an enumerated list of upper-case verbs.
type MapBacked struct {
	exchanges []recorder.Exchange
}

// New returns the defective recorder.
func New() *MapBacked { return &MapBacked{} }

// Record collapses repeated field names and normalises the method token.
func (m *MapBacked) Record(method, rawTarget []byte, fields []recorder.Field, body []byte) {
	collapsed := map[string]string{}
	order := []string{}
	for _, f := range fields {
		key := strings.ToLower(f.Name)
		if _, seen := collapsed[key]; !seen {
			order = append(order, key)
		}
		collapsed[key] = f.Value
	}
	out := make([]recorder.Field, 0, len(order))
	for _, key := range order {
		out = append(out, recorder.Field{Name: key, Value: collapsed[key]})
	}
	sum := sha256.Sum256(body)
	m.exchanges = append(m.exchanges, recorder.Exchange{
		Method:    []byte(strings.ToUpper(string(method))),
		RawTarget: append([]byte(nil), rawTarget...),
		Fields:    out,
		Body:      append([]byte(nil), body...),
		Digest:    hex.EncodeToString(sum[:]),
		Length:    len(body),
	})
}

// Exchanges returns what was recorded.
func (m *MapBacked) Exchanges() []recorder.Exchange { return m.exchanges }
