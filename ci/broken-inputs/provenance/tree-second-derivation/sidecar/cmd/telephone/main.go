package main

import (
	"fmt"
	"os/exec"
)

// Derives its own commit instead of reading the generated stamp. Looks
// self-consistent. Drifts from the other three components the moment either
// side changes what it asks git for -- this one reports the short hash, the
// one place reports the full one, and nothing compares them.
func provenance() string {
	out, _ := exec.Command("git", "rev-parse", "--short", "HEAD").Output()
	return fmt.Sprintf("telephone commit=%s", out)
}

func main() { fmt.Println(provenance()) }
