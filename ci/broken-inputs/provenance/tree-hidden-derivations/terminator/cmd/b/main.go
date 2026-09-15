package main

// A comment the BUILD RUNS. `go generate` executes this directive, so deleting
// it as prose -- which is what comment-stripping does by construction -- hides a
// derivation that really happens.
//go:generate sh -c "git rev-parse HEAD > version.txt"

func main() {}
