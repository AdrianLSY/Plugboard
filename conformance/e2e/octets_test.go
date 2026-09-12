//go:build gating

package e2e

import (
	"context"
	"testing"
	"time"

	"plugboard/conformance/harness"
	"plugboard/conformance/recorder"
)

// THE FIRST TEST. A body of arbitrary octets is POSTed through the client edge
// and the recording origin's digest and octet count are asserted equal to the
// client's -- at the origin's recording alone, so the assertion is satisfiable
// before any response path exists.
//
// The assertion the prior attempt never had. Its suite ran 27,000 lines and
// never noticed that request bodies arrived empty, because no test compared what
// was sent to what arrived.
func TestRequestOctetsReachTheOriginIntact(t *testing.T) {
	body := recorder.Pattern(BodyOctets)
	if len(body) != BodyOctets {
		t.Fatalf("the fixture is %d octets, want %d", len(body), BodyOctets)
	}
	wantDigest := recorder.Digest(body)

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	origin := buildRecordingOrigin(t)
	dir := t.TempDir()
	h, err := harness.Start(ctx, dir, chain(t, origin, "--record-dir", dir))
	if err != nil {
		// This is the expected outcome today, and the diagnostic is the finding:
		// it names the process that is not there. An assertion reached with an
		// empty body and passing would be worse than useless.
		t.Fatalf("the chain did not start, so nothing was measured: %v", err)
	}
	defer h.Stop()

	edge, err := h.Address("proxy")
	if err != nil {
		t.Fatalf("the client edge has no address: %v", err)
	}
	recorded := postAndRead(t, edge, dir, body)
	if recorded.Length != len(body) {
		t.Errorf("the origin recorded %d octet(s), the client sent %d",
			recorded.Length, len(body))
	}
	if recorded.Digest != wantDigest {
		t.Errorf("the origin recorded digest %s, the client sent %s -- the bytes "+
			"changed somewhere in the chain", recorded.Digest, wantDigest)
	}
}

// The response-direction twin. The origin emits a body of arbitrary octets and
// the raw client asserts digest and length equality.
func TestResponseOctetsReachTheClientIntact(t *testing.T) {
	want := recorder.Pattern(BodyOctets)
	wantDigest := recorder.Digest(want)

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	origin := buildRecordingOrigin(t)
	dir := t.TempDir()
	h, err := harness.Start(ctx, dir,
		chain(t, origin, "--emit-bytes", itoa(BodyOctets)))
	if err != nil {
		t.Fatalf("the chain did not start, so nothing was measured: %v", err)
	}
	defer h.Stop()

	edge, err := h.Address("proxy")
	if err != nil {
		t.Fatalf("the client edge has no address: %v", err)
	}
	got := getAndRead(t, edge)
	if len(got) != len(want) {
		t.Errorf("the client received %d octet(s), the origin emitted %d",
			len(got), len(want))
	}
	if digest := recorder.Digest(got); digest != wantDigest {
		t.Errorf("the client received digest %s, the origin emitted %s",
			digest, wantDigest)
	}
}
