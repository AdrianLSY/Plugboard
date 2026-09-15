//go:build integration

package main

import (
	"context"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"

	"plugboard/conformance/harness"
	"plugboard/conformance/internal/buildstamp"
)

// The instrument reports which build it is, and reports it from the generated
// stamp rather than from a copy of one.
//
// It did neither. `build_stamp.go` was committed, carried a `map[string]string`
// frozen at the commit it was generated on, and `make stamp` never rewrote it --
// ci/make/go.mk writes `internal/buildstamp/stamp.go` and nothing else. The
// function reading that map was called by no main, only by its own test, and
// that test compared the function's output against the same map the function
// read, so any value whatsoever passed and the staleness was unobservable.
//
// Asserted by STARTING THE BINARY and reading what it actually said, not by
// calling a function the test also supplies the expectation for. That is the
// distinction the previous test missed, and it is the whole reason this one is
// in the integration tier rather than the fast one.
func TestTheRecordingOriginReportsTheGeneratedStampAtStartup(t *testing.T) {
	binary := buildTheOrigin(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	h, err := harness.Start(ctx, t.TempDir(),
		[]harness.Spec{{Name: "recording-origin", Path: binary}})
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

// buildTheOrigin compiles the binary under test from the module it lives in, so
// the stamp it links is the one `make stamp` generated for this run rather than
// whatever a previous build left behind.
func buildTheOrigin(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("cannot locate this source file, so the module root is unknown")
	}
	module, err := filepath.Abs(filepath.Join(filepath.Dir(file), "..", ".."))
	if err != nil {
		t.Fatalf("resolving the module root: %v", err)
	}
	out := filepath.Join(t.TempDir(), "recording-origin")
	if runtime.GOOS == "windows" {
		out += ".exe"
	}
	//nolint:gosec // G204: the only variable is a path this function just made
	// under t.TempDir(); the command and its package are literals.
	cmd := exec.CommandContext(t.Context(), "go", "build", "-o", out, "./cmd/recording-origin")
	cmd.Dir = module
	if combined, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("building the recording origin: %v\n%s", err, combined)
	}
	return out
}
