//go:build integration

package recorder_test

import (
	"os/exec"
	"path/filepath"
	"testing"
)

// The instrument's discrimination is demonstrated by a SEPARATE module holding a
// deliberately defective recorder, and this is what makes that demonstration run
// rather than sit in the tree. ci/broken-inputs is a declared scan exclusion, so
// nothing there is reachable from a component's build; the proof has to be
// pulled in from this side or it is never performed.
//
// Integration tier rather than fast: it compiles and runs another module, which
// is a process and a build, and the fast tier's budget is a correctness control
// rather than a target.
func TestTheAssertionSuiteIsProvenToRejectAWrongRecorder(t *testing.T) {
	fixture, err := filepath.Abs(filepath.Join("..", "..", "ci", "broken-inputs", "recording-origin"))
	if err != nil {
		t.Fatalf("locating the violating input: %v", err)
	}
	cmd := exec.CommandContext(t.Context(), "go", "test", "-race", "./...")
	cmd.Dir = fixture
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("the violating input's own tests did not pass, so the assertion "+
			"suite is no longer proven to reject a wrong recorder:\n%s", out)
	}
}
