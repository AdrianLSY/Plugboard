// The module path is internal: nothing here is published, and no `go get` ever
// resolves it. It becomes a host path in one edit if the repository ever gains a
// remote -- see docs/code/languages/go.md.
module plugboard/sidecar

go 1.27
