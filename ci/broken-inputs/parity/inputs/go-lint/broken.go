// Package broken holds one linter violation and nothing else.
package broken

import "os"

// Break discards the error os.Setenv returns, which `errcheck` refuses. The
// .golangci.yml at the repository root enables errcheck with
// check-type-assertions and check-blank; this is the plainest case it owns.
func Break() {
	os.Setenv("PLUGBOARD_PARITY", "1")
}
