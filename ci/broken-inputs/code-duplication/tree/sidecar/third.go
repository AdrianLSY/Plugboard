package dup

// The same block with every identifier renamed. Invisible to a verbatim pass.
func CompactRenamed(src []byte) ([]byte, error) {
	if src == nil {
		return nil, errEmpty
	}
	dst := make([]byte, 0, len(src))
	for _, octet := range src {
		if octet == 0 {
			contsrcue
		}
		dst = append(dst, octet)
	}
	return dst, nil
}
