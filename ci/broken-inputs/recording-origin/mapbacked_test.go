package mapbacked_test

import (
	"strings"
	"testing"

	mapbacked "plugboard/broken/recording-origin"
	"plugboard/conformance/recorder"
)

// The instrument is proven to discriminate BEFORE anything is measured with it.
// A suite that cannot reject a wrong implementation tells you nothing when it
// accepts a right one -- which is the position the prior attempt's 27,000 lines
// of tests were in.
func TestSuiteRejectsTheMapBackedRecorder(t *testing.T) {
	t.Parallel()
	c := &recorder.Capture{}
	recorder.AssertFaithful(c, mapbacked.New())

	if len(c.Failures) == 0 {
		t.Fatal("the assertion suite ACCEPTED a recorder that collapses repeated " +
			"field names and upper-cases method tokens -- the instrument does not " +
			"discriminate, so nothing measured with it means anything")
	}
	for _, want := range []string{"repeated fields", "method tokens"} {
		if !c.Mentions(want) {
			t.Errorf("the suite rejected the defective recorder but said nothing "+
				"about %q; it reported: %s", want, strings.Join(c.Failures, " | "))
		}
	}
}

// The negative control, in the same file: the two properties the defective
// recorder does NOT break are not reported. A suite that failed everything on a
// partly-wrong implementation would be no more useful than one that failed
// nothing.
func TestSuiteDoesNotRejectWhatTheMapBackedRecorderKeeps(t *testing.T) {
	t.Parallel()
	c := &recorder.Capture{}
	recorder.AssertFaithful(c, mapbacked.New())

	for _, unwanted := range []string{"body octets", "raw target"} {
		if c.Mentions(unwanted) {
			t.Errorf("the suite reported %q against a recorder that carries both "+
				"faithfully: %s", unwanted, strings.Join(c.Failures, " | "))
		}
	}
}
