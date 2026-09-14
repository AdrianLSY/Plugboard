package violating

// An unchecked type assertion. errcheck runs with check-type-assertions, which
// the reference's own config set and which task 2.3 ports: a bare v.(string)
// panics on the first value that is not one, and the panic is in a proxy.
func Unchecked(v any) string { return v.(string) }
