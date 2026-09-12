// A deliberately defective recorder, and the proof that the assertion suite
// rejects it. Its own module, because ci/broken-inputs is a declared scan
// exclusion and nothing here may be reachable from a component's build.
module plugboard/broken/recording-origin

go 1.27

require plugboard/conformance v0.0.0

replace plugboard/conformance => ../../../conformance
