package violating

// Deliberately misformatted: gofmt is a FORMATTER, and golangci-lint reports a
// file it would rewrite as an issue rather than rewriting it. That distinction
// is the whole of task 3.2 -- `go fmt` rewrites and therefore checks nothing.
func  Spaced( a int )  int {
return a+1
}
