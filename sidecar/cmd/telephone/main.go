// Command telephone is the sidecar: the program a tenant runs beside their own
// backend. It dials out to the proxy, so the tenant needs no inbound network
// path and no listening port.
//
// Skeleton only. What it will own is stated once, in
// docs/code/boundaries/sidecar.md, and its behaviour is owned by the
// sidecar/program specification. Neither is restated here.
package main

import (
	"fmt"
	"os"

	"plugboard/sidecar/internal/buildstamp"

	"plugboard/sidecar/internal/tunnel"
)

func main() {
	if _, err := fmt.Fprintln(os.Stdout, buildstamp.Line()); err != nil {
		os.Exit(1)
	}
	if _, err := fmt.Fprintln(os.Stdout, tunnel.Banner()); err != nil {
		os.Exit(1)
	}
}
