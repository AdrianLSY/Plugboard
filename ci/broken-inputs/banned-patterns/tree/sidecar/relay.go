package relay

import "io"

// Two planted defects: a one-value-per-name container over header fields, and a
// body accumulated before any of it is emitted.
type Response struct {
	headers map[string]string
}

func Relay(body io.Reader) ([]byte, error) {
	return io.ReadAll(body)
}
