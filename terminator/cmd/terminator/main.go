// Command terminator is the client-facing edge D16 puts in v1: it terminates
// HTTP/2 from clients, which Bandit cannot, and gains HTTP/3 and WebTransport
// when those ship.
//
// It is a contract speaker, not a second proxy. Skeleton only; the boundary is
// stated once in docs/code/boundaries/terminator.md.
//
// The one thing it already reports is its own build. startupReport and the stamp
// it renders come from build_stamp.go, which `make stamp` generates from the
// single stamping place in ci/make/go.mk.
package main

import (
	"fmt"
	"os"
)

// banner is what this command says about itself before it says what it was
// built from.
const banner = "plugboard terminator: no contract implementation yet"

func main() {
	if _, err := fmt.Fprintln(os.Stdout, startupReport(banner)); err != nil {
		os.Exit(1)
	}
}
