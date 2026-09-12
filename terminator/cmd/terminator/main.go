// Command terminator is the client-facing edge D16 puts in v1: it terminates
// HTTP/2 from clients, which Bandit cannot, and gains HTTP/3 and WebTransport
// when those ship.
//
// It is a contract speaker, not a second proxy. Skeleton only; the boundary is
// stated once in docs/code/boundaries/terminator.md.
package main

import (
	"fmt"
	"os"
)

func main() {
	if _, err := fmt.Fprintln(os.Stdout, "plugboard terminator: no contract implementation yet"); err != nil {
		os.Exit(1)
	}
}
