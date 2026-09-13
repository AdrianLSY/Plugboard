package main

import "testing"

// The second binary this component ships, and the one a recorded exchange is
// attributed to. It is a separate `package main` compiling its OWN generated
// build_stamp.go -- `make stamp` writes two, one per cmd/ directory -- so every
// assertion the suite's test makes about the suite's stamp reaches nothing here.
// Until this file existed, this binary's stamp was asserted by nothing at all
// while the component as a whole looked covered: ci/gates/provenance.py's case 4
// asks whether some test under the component exercises the reporter, and the
// suite's own test answered it.
//
// `component=conformance` and not `recording-origin`: the field names the
// COMPONENT, and both binaries are that one component. conformance/Makefile
// leaves STAMP_COMPONENT at its default for exactly that reason, and this literal
// is what pins the decision -- if the second stamping invocation ever starts
// passing a name of its own, this test fails rather than the recordings quietly
// starting to cite a component that does not exist.
func TestRecordingOriginReportsItsGeneratedStampAtStartup(t *testing.T) {
	want := "probe\nbuild-provenance component=conformance version=" + buildStamp["version"] +
		" commit=" + buildStamp["commit"] + " tree=" + buildStamp["tree"] + " built_at=" + buildStamp["built_at"]
	if got := startupReport("probe"); got != want {
		t.Fatalf("the recording origin reports\n  %q\nand was stamped\n  %q", got, want)
	}
}
