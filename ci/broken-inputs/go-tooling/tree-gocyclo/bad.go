package violating

// Cyclomatic complexity 20 against a ceiling of 15. The reference's 813-line
// render/1 is the case this makes unwritable; twenty branches is the smallest
// input that crosses the line the config sets.
func Tangled(n int) int {
	t := 0
	if n > 1 {
		t++
	}
	if n > 2 {
		t++
	}
	if n > 3 {
		t++
	}
	if n > 4 {
		t++
	}
	if n > 5 {
		t++
	}
	if n > 6 {
		t++
	}
	if n > 7 {
		t++
	}
	if n > 8 {
		t++
	}
	if n > 9 {
		t++
	}
	if n > 10 {
		t++
	}
	if n > 11 {
		t++
	}
	if n > 12 {
		t++
	}
	if n > 13 {
		t++
	}
	if n > 14 {
		t++
	}
	if n > 15 {
		t++
	}
	if n > 16 {
		t++
	}
	if n > 17 {
		t++
	}
	if n > 18 {
		t++
	}
	if n > 19 {
		t++
	}
	return t
}
