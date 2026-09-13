package main

import "testing"

// This binary is the one that leaves the building: five cross-compiled artifacts
// ship from `make build`, and the account each gives of its own build is the only
// account its recipient has. So the field names and their order are literals here
// rather than values read back out of the stamp -- a field the stamp quietly
// stopped carrying would otherwise be invisible from both sides at once.
//
// `component=conformance` is a LITERAL, and that is the repair. This test used to
// read `component=" + buildStamp["component"] + "`, which put the value under
// test on both sides of the comparison: it cancelled, and only the field names
// survived as an assertion. Measured, in that form: a stamp with all five values
// blanked left `go test ./cmd/conformance` reporting `ok`.
//
// It mattered most here of anywhere. This is the binary handed to a contributor
// writing a sidecar in a language this repository has never seen; they did not
// build it, cannot rebuild it, and the line it prints at startup is the whole of
// what they can know about which tree it came from. A blank or mislabelled stamp
// is not a cosmetic defect in that artifact -- it is a conformance result
// attributed to a revision nobody can identify.
//
// The value SHAPES are asserted in ci/gates/provenance.py against the stamp the
// one place emits when RUN, rather than compiled into each module as another
// snapshot of a format owned elsewhere. What cannot live there is which component
// this binary believes it is, so that is what is pinned here.
func TestConformanceReportsItsGeneratedStampAtStartup(t *testing.T) {
	want := "probe\nbuild-provenance component=conformance version=" + buildStamp["version"] +
		" commit=" + buildStamp["commit"] + " tree=" + buildStamp["tree"] + " built_at=" + buildStamp["built_at"]
	if got := startupReport("probe"); got != want {
		t.Fatalf("the suite reports\n  %q\nand was stamped\n  %q", got, want)
	}
}
