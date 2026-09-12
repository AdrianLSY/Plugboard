// Package e2e holds the two gating tests: a body of arbitrary octets crossing
// the whole chain, once in each direction, asserted on the exact bytes.
//
// They are written BEFORE the proxy exists and they are expected to be RED. That
// is the point. rebuild-plugboard's own cost analysis says 270 of 727 tasks land
// before the streaming spine begins and 406 before a response body first reaches
// a client, and it carries three obligations to survive that ordering. The first
// is this one: the two exact-bytes gates are committed red from task 4.3 onward,
// so the gap is visible from the first week rather than discovered at section 38.
//
// They carry their own build tag so the ordinary tiers do not run them. A
// permanently red test inside `make test-integration` makes every later change
// unmergeable; instead ci/expected-outcomes.py runs them and compares each
// outcome to a recorded baseline, failing when one differs IN EITHER DIRECTION.
package e2e

import (
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"

	"plugboard/conformance/harness"
)

// BodyOctets is the size task 4.3 fixes: a literal 1 MiB, chosen here rather
// than derived from the contract's floor frame payload, which task 9.1 does not
// define until five sections later. Stated so this file carries no forward
// dependency and could be merged first, as the task claims.
const BodyOctets = 1 << 20

// repoRoot is this file's directory, two levels up.
func repoRoot(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("cannot locate this source file, so the repository root is unknown")
	}
	root, err := filepath.Abs(filepath.Join(filepath.Dir(file), "..", ".."))
	if err != nil {
		t.Fatalf("resolving the repository root: %v", err)
	}
	return root
}

// buildRecordingOrigin builds the instrument. It is the one process in the chain
// that exists today, and building it here rather than depending on a checked-in
// binary keeps the test honest about which parts are real.
func buildRecordingOrigin(t *testing.T) string {
	t.Helper()
	out := filepath.Join(t.TempDir(), "recording-origin")
	if runtime.GOOS == "windows" {
		out += ".exe"
	}
	//nolint:gosec // G204: the only variable here is a path this function just
	// created under t.TempDir(); the command and its package are literals.
	cmd := exec.CommandContext(t.Context(), "go", "build", "-o", out, "./cmd/recording-origin")
	cmd.Dir = filepath.Join(repoRoot(t), "conformance")
	if combined, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("building the recording origin: %v\n%s", err, combined)
	}
	return out
}

// chain returns the processes an end-to-end case needs, in the order a request
// crosses them. The proxy is first, so a run says the proxy is absent before it
// says anything about the hops behind it.
func chain(t *testing.T, origin string, originArgs ...string) []harness.Spec {
	t.Helper()
	root := repoRoot(t)
	return []harness.Spec{
		{Name: "proxy", Path: filepath.Join(root, "proxy", "_build", "prod", "rel",
			"plugboard", "bin", "plugboard")},
		{Name: "sidecar", Path: filepath.Join(root, "sidecar", "telephone")},
		{Name: "recording-origin", Path: origin, Args: originArgs},
	}
}
