package recorder_test

import (
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

func TestPersistWritesOneFilePerExchange(t *testing.T) {
	t.Parallel()
	r := recorder.NewOrdered()
	r.Record([]byte("POST"), []byte("/a"), nil, recorder.AllOctets())
	r.Record([]byte("GET"), []byte("/b"), nil, nil)
	dir := t.TempDir()
	if err := recorder.Persist(dir, r.Exchanges()); err != nil {
		t.Fatalf("Persist: %v", err)
	}
	for _, name := range []string{"exchange-0000.json", "exchange-0001.json"} {
		if _, err := readFile(dir, name); err != nil {
			t.Errorf("Persist wrote no %s: %v", name, err)
		}
	}
}
