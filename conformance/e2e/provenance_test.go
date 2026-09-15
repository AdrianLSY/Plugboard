//go:build integration

package e2e

import (
	"context"
	"strings"
	"testing"
	"time"

	"plugboard/conformance/harness"
	"plugboard/conformance/internal/buildstamp"
)

// The instrument reports which build it is, and reports it from the generated
// stamp rather than from a copy of one.
//
// It did neither. `cmd/recording-origin/build_stamp.go` was committed, carried a
// `map[string]string` frozen at the commit it was generated on, and `make stamp`
// never rewrote it -- ci/make/go.mk writes `internal/buildstamp/stamp.go` and
// nothing else. The function reading that map was called by no main, only by its
// own test, and that test built its expectation FROM the same map the function
// read, so any values passed and the staleness was unobservable.
//
// Asserted by STARTING THE BINARY and reading what it actually said, against an
// expectation taken from the generated package rather than from a literal this
// file also supplies. That is the distinction the previous test collapsed.
//
// It lives beside the other cases that start this binary because the builder does:
// written in cmd/recording-origin it was a renamed copy of buildRecordingOrigin,
// and `code-duplication` refused it by name. A renamed copy is a copy.
func TestTheRecordingOriginReportsTheGeneratedStampAtStartup(t *testing.T) {
	origin := buildRecordingOrigin(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	h, err := harness.Start(ctx, t.TempDir(),
		[]harness.Spec{{Name: "recording-origin", Path: origin}})
	if err != nil {
		t.Fatalf("the origin did not start: %v", err)
	}
	defer h.Stop()

	// Polled, not read once. The harness returns the instant the readiness file
	// exists, and the parent's copy of the child's pipe lags that by however long
	// the scheduler takes -- so a single read races the process's own first line
	// and this case would fail intermittently against a correct binary. Polling
	// observes; it starts nothing and repairs nothing.
	want := buildstamp.Line()
	got := h.Output("recording-origin")
	for deadline := time.Now().Add(10 * time.Second); !strings.Contains(got, want); {
		if time.Now().After(deadline) {
			t.Fatalf("the origin ran for ten seconds and said:\n  %s\nwhich does not "+
				"carry its generated provenance:\n  %s\nA binary that reports no build "+
				"is one nobody can pair with a recording after the fact, and a binary "+
				"reporting a stamp it carries its own copy of reports whichever build "+
				"last wrote that copy", strings.TrimSpace(got), want)
		}
		time.Sleep(5 * time.Millisecond)
		got = h.Output("recording-origin")
	}
}
