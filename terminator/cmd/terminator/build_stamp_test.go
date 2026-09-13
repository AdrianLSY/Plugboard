package main

import "testing"

// The five field names and their order are written out here as literals rather
// than read back out of the stamp. A test that takes its expectation from the
// artifact under test cannot notice that artifact renaming, reordering or
// dropping a field, which is every way a stamp goes quietly wrong.
//
// `component=terminator` is a LITERAL for the same reason, and it is the line
// that matters. This test used to read `component=" + buildStamp["component"] +
// "`, which put the value under test on both sides of the comparison: it
// cancelled, and what was left asserted the field names and nothing about what
// they were set to. Measured, in that form: a stamp with all five values blanked
// and a stamp reading `component=WRONG-NOT-TERMINATOR` both left
// `go test ./cmd/terminator` reporting `ok`. With the name written out, both
// fail here -- this binary now says which component it believes it is, and is
// held to it.
//
// The reasoning that produced the weaker form is worth recording because it is
// plausible: one recipe (ci/make/go.mk) stamps all four components, so binding
// values once, in the sidecar's test, looks like avoiding duplication. One
// recipe does stamp all four; one ARTIFACT does not. Each component is a
// separate Go module compiling its own generated build_stamp.go, so the
// sidecar's test binds the sidecar's compiled-in values and reaches nothing
// here. A shared recipe is not a shared artifact.
//
// The value SHAPES -- that the commit is forty hex digits, that the tree marker
// is one of three words, that no field is blank -- are asserted in
// ci/gates/provenance.py, against the stamp the one place actually emits when it
// is RUN, rather than compiled into four modules as four snapshots of one
// format. They are not asserted per component here because that format is owned
// in one place and a fourth copy of it would be a copy
// (docs/code/rules/duplication-threshold.md). What cannot live there is which
// component this binary is, so that is what lives here.
func TestTerminatorReportsItsGeneratedStampAtStartup(t *testing.T) {
	want := "probe\nbuild-provenance component=terminator version=" + buildStamp["version"] +
		" commit=" + buildStamp["commit"] + " tree=" + buildStamp["tree"] + " built_at=" + buildStamp["built_at"]
	if got := startupReport("probe"); got != want {
		t.Fatalf("the terminator reports\n  %q\nand was stamped\n  %q", got, want)
	}
}
