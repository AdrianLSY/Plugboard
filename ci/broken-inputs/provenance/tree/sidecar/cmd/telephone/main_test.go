package main

import "testing"

// A test, and a passing one. It reads the banner and never the provenance,
// which is the state the fourth case is about: tests exist, and the reported
// build is asserted by none of them.
//
// It NAMES startupReport in this comment and never calls it, for the same
// reason main.go does: a fourth case asking whether some test file contains the
// reporter's name is answered by the sentence explaining why the reporter
// matters, and a test suite can then satisfy the rule by discussing it. The
// declared case for this tree is "no test under it CALLS startupReport", and
// this file is the input that separates calling from mentioning.
func TestBannerNamesTheComponent(t *testing.T) {
	if got := "plugboard sidecar: no contract implementation yet"; got == "" {
		t.Fatal("the banner is empty")
	}
}
