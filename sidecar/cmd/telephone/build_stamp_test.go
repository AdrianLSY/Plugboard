package main

import (
	"regexp"
	"testing"
)

// The five field names and their order are literals here rather than values read
// back out of the stamp: an expectation taken from the artifact under test cannot
// notice that artifact renaming, reordering or dropping a field.
//
// `component=sidecar` is a literal for the stronger version of the same reason.
// Written as `component=" + buildStamp["component"] + "`, the value under test
// sits on both sides of the comparison and cancels, leaving the field names
// asserted and their contents not. The component name is the one value this
// module knows without asking the stamp, so it is the one written out.
func TestSidecarReportsItsGeneratedStampAtStartup(t *testing.T) {
	want := "probe\nbuild-provenance component=sidecar version=" + buildStamp["version"] +
		" commit=" + buildStamp["commit"] + " tree=" + buildStamp["tree"] + " built_at=" + buildStamp["built_at"]
	if got := startupReport("probe"); got != want {
		t.Fatalf("the sidecar reports\n  %q\nand was stamped\n  %q", got, want)
	}
}

// The value shapes as a COMPILED-IN artifact sees them. This is the one module
// that carries them, and it is deliberately the only one: the shape of a stamp
// field is a property of the recipe that emits it, not of any binary it lands
// in, so four modules each repeating these five patterns would be four copies of
// one thing (docs/code/rules/duplication-threshold.md) and four snapshots of
// whatever the recipe emitted on the day each was pasted.
//
// The authority for the shapes is therefore ci/gates/provenance.py, which holds
// them against the stamp the one place emits when it is RUN. What this test adds
// is the other end of the same claim: that the values which actually reached a
// compiled binary still look like that. What each component's own test binds,
// above, is the one value no shared place can know -- which component it is.
//
// That the dirty marker actually MOVES with the tree is ci/gates/provenance.py's
// case too: no compiled-in value can demonstrate it.
func TestStampValuesHaveTheShapesTheStampingPlacePromises(t *testing.T) {
	for name, shape := range map[string]*regexp.Regexp{
		"component": regexp.MustCompile(`^sidecar$`),
		"version":   regexp.MustCompile(`^\S+$`),
		"commit":    regexp.MustCompile(`^([0-9a-f]{40}|unknown)$`),
		"tree":      regexp.MustCompile(`^(clean|dirty|unknown)$`),
		"built_at":  regexp.MustCompile(`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`),
	} {
		if !shape.MatchString(buildStamp[name]) {
			t.Errorf("stamp field %s is %q, which does not match %s -- provenance is a "+
				"value of the promised shape, or the word unknown, never something that "+
				"merely resembles one", name, buildStamp[name], shape)
		}
	}
	if len(buildStamp) != len(buildStampOrder) {
		t.Errorf("the stamp carries %d field(s) and reports %d", len(buildStamp), len(buildStampOrder))
	}
}
