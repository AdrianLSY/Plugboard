// Command conformance runs the suite that is the authority on the wire
// contract, against any implementation in any language.
//
// Skeleton only: the fixture corpus is written before the code it gates
// (rebuild-plugboard section 12), and this binary exists first so the corpus has
// something to be carried by.
package main

import (
	"fmt"
	"os"
)

func main() {
	if _, err := fmt.Fprintln(os.Stdout, "plugboard conformance suite: no cases yet"); err != nil {
		os.Exit(1)
	}
}
