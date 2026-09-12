// Package tunnel will hold the sidecar's half of the wire contract.
//
// It is empty of contract code on purpose: the schema is frozen before any
// implementation speaks it (rebuild-plugboard section 17), and a hand-written
// codec landing first is exactly the "two independent fictions" the conformance
// suite exists to remove.
package tunnel

// Banner is a placeholder so the package compiles and the skeleton is provably
// buildable. It is deleted by the first task that puts real code here.
func Banner() string {
	return "plugboard sidecar: no contract implementation yet"
}
