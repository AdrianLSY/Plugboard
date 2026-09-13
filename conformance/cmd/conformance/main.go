// Command conformance runs the suite that is the authority on the wire
// contract, against any implementation in any language.
//
// Skeleton only: the fixture corpus is written before the code it gates
// (rebuild-plugboard section 12), and this binary exists first so the corpus has
// something to be carried by.
//
// This binary is handed to someone who did not build it -- five cross-compiled
// artifacts ship from `make build` -- so what it says about its own build is the
// only account of it the recipient has. startupReport and the stamp it renders
// are generated into build_stamp.go by `make stamp`, from the one place that
// stamps every component (ci/make/go.mk).
package main

import (
	"fmt"
	"os"
)

// banner is what the suite says about itself before it says what it was built
// from.
const banner = "plugboard conformance suite: no cases yet"

func main() {
	if _, err := fmt.Fprintln(os.Stdout, startupReport(banner)); err != nil {
		os.Exit(1)
	}
}
