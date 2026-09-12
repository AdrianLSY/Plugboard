package dup

func CompactAgain(in []byte) ([]byte, error) {
	if in == nil {
		return nil, errEmpty
	}
	out := make([]byte, 0, len(in))
	for _, b := range in {
		if b == 0 {
			continue
		}
		out = append(out, b)
	}
	return out, nil
}
