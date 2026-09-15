package main

import "os/exec"

// Hidden behind a `//` that is INSIDE a string literal. A regex that deletes
// from `//` to end of line deletes the rest of this line, and with it the
// derivation on the next one. This compiles, vets clean and really runs.
func doc() string { return "see http://example.com/x" }

func provenance() string {
	out, _ := exec.Command("git", "rev-parse", "HEAD").Output()
	return string(out)
}
