package recorder_test

import (
	"encoding/json"
	"testing"

	"plugboard/conformance/recorder"
)

// The instrument passes its own suite. This is the control; the demonstration
// that the suite can REJECT an implementation is in
// ci/broken-inputs/recording-origin, and it is the half that matters.
func TestOrderedIsFaithful(t *testing.T) {
	t.Parallel()
	recorder.AssertFaithful(t, recorder.NewOrdered())
}

func TestAllOctetsCarriesEveryValueAndALoneContinuationByte(t *testing.T) {
	t.Parallel()
	body := recorder.AllOctets()
	if len(body) != 257 {
		t.Errorf("AllOctets is %d bytes, want 257 (every value, then a lone 0x80)", len(body))
	}
	seen := map[byte]int{}
	for _, b := range body {
		seen[b]++
	}
	if len(seen) != 256 {
		t.Errorf("AllOctets covers %d distinct values, want 256", len(seen))
	}
	if seen[0x80] != 2 {
		t.Errorf("AllOctets carries 0x80 %d time(s), want 2 -- once in sequence and "+
			"once alone, where it is a continuation byte with no lead byte", seen[0x80])
	}
}

// Each file is read back, not only found. The recordings on disk are what e2e's
// assertions read, and checking that the files existed passed a Persist that
// wrote `"chunked": false` for every exchange -- so the flag that says a body
// arrived chunked is asserted in both directions, beside the digest and the
// octet count those assertions compare.
func TestPersistWritesOneFilePerExchange(t *testing.T) {
	t.Parallel()
	body := recorder.AllOctets()
	r := recorder.NewOrdered()
	r.RecordChunked([]byte("POST"), []byte("/a"), nil, body)
	r.Record([]byte("GET"), []byte("/b"), nil, nil)
	dir := t.TempDir()
	if err := recorder.Persist(dir, r.Exchanges()); err != nil {
		t.Fatalf("Persist: %v", err)
	}
	for _, want := range []struct {
		name, digest string
		octets       int
		chunked      bool
	}{
		{name: "exchange-0000.json", digest: recorder.Digest(body), octets: len(body), chunked: true},
		{name: "exchange-0001.json", digest: recorder.Digest(nil), octets: 0, chunked: false},
	} {
		blob, err := readFile(dir, want.name)
		if err != nil {
			t.Errorf("Persist wrote no %s: %v", want.name, err)
			continue
		}
		var got struct {
			Digest  string `json:"digest_sha256"`
			Octets  int    `json:"octet_count"`
			Chunked bool   `json:"chunked"`
		}
		if err := json.Unmarshal(blob, &got); err != nil {
			t.Errorf("%s is not the persisted shape: %v", want.name, err)
			continue
		}
		if got.Digest != want.digest || got.Octets != want.octets || got.Chunked != want.chunked {
			t.Errorf("%s holds digest %s, %d octet(s), chunked %t; recorded %s, %d, %t",
				want.name, got.Digest, got.Octets, got.Chunked, want.digest, want.octets, want.chunked)
		}
	}
}
