package main

// Reading a request body in the framing its fields declare, and refusing every
// framing this instrument does not read. Split from main.go along the one
// responsibility that grew when chunked transfer coding arrived.

import (
	"bufio"
	"bytes"
	"errors"
	"fmt"
	"io"
	"strconv"
	"strings"

	"plugboard/conformance/recorder"
)

// errInvalidFraming marks a message whose framing is not merely unsupported but
// malformed. serve answers 400 for it and 501 for errUnimplemented, framing this
// instrument simply does not implement, because "your message is invalid" and
// "I do not do that" are different answers and a sender can act on only one.
var (
	errInvalidFraming = errors.New("invalid message framing")
	errUnimplemented  = errors.New("framing this instrument does not implement")
)

// readBody reads exactly the body the fields declare, or refuses.
//
// It resolves nothing. Two Content-Length fields are refused rather than reduced
// to one, EVEN WHERE THEY AGREE -- RFC 9112 6.3 permits collapsing an identical
// pair, and this instrument declines the permission, because collapsing is
// normalising and the package this serves is documented as normalising nothing.
// The value is read as a count of octets and nothing else: no sign, no list, no
// surrounding space, so `-5`, `+5` and `5, 5` are each refused rather than
// silently becoming 5, -5 or a body that was never read.
//
// A transfer coding is read only when it is exactly one chunked coding. A
// Transfer-Encoding beside a Content-Length is the other request-smuggling shape
// and is refused as invalid, whatever either says; a coding other than a single
// chunked one -- gzip, a list, a second field -- is refused as unimplemented.
func readBody(br *bufio.Reader, fields []recorder.Field) (body []byte, chunked bool, err error) {
	declared := make([]string, 0, 1)
	codings := make([]string, 0, 1)
	for _, f := range fields {
		switch strings.ToLower(f.Name) {
		case "transfer-encoding":
			codings = append(codings, f.Value)
		case "content-length":
			declared = append(declared, f.Value)
		}
	}
	if len(codings) > 0 && len(declared) > 0 {
		return nil, false, fmt.Errorf("%w: transfer-encoding %q beside content-length %q "+
			"-- the second request-smuggling shape, where which framing a hop believes is "+
			"the whole defect, so this instrument records neither",
			errInvalidFraming, strings.Join(codings, ", "), strings.Join(declared, ", "))
	}
	if len(codings) > 0 {
		if len(codings) != 1 || !strings.EqualFold(codings[0], "chunked") {
			return nil, false, fmt.Errorf("%w: transfer-encoding %q -- this instrument "+
				"reads a single chunked coding and nothing else, and refuses rather than "+
				"guessing at a body it cannot frame", errUnimplemented, strings.Join(codings, ", "))
		}
		body, err = readChunked(br)
		return body, err == nil, err
	}
	body, err = readLength(br, declared)
	return body, false, err
}

func readLength(br *bufio.Reader, declared []string) ([]byte, error) {
	if len(declared) > 1 {
		return nil, fmt.Errorf("%w: more than one content-length field (%s) -- this is "+
			"one of the two request-smuggling shapes, and which one a hop believes is "+
			"the whole defect, so this instrument records neither",
			errInvalidFraming, strings.Join(declared, ", "))
	}
	if len(declared) == 0 {
		return nil, nil
	}
	length, err := octetCount(declared[0])
	if err != nil {
		return nil, fmt.Errorf("%w: content-length %q is not a count of octets (%v) -- "+
			"read as one it would frame a body nobody sent", errInvalidFraming, declared[0], err)
	}
	var body bytes.Buffer
	if err := copyOctets(&body, br, length); err != nil {
		return nil, err
	}
	return body.Bytes(), nil
}

// copyOctets appends exactly n octets from br to dst. The buffer grows as octets
// arrive rather than being allocated from n: a peer states that number, and this
// instrument is pointed at adversarial inputs by design.
func copyOctets(dst *bytes.Buffer, br *bufio.Reader, n int64) error {
	if read, err := io.CopyN(dst, br, n); err != nil {
		// io.CopyN reports a short read as io.EOF, and run() suppresses io.EOF so
		// an ordinary connection close between requests stays quiet. A body that
		// stopped early is the opposite of a quiet end, so it is restated as what
		// it is -- which is also what io.ReadFull said here before this read
		// stopped pre-allocating.
		if errors.Is(err, io.EOF) {
			err = fmt.Errorf("%w after %d of them", io.ErrUnexpectedEOF, read)
		}
		return fmt.Errorf("reading %d body octet(s): %w", n, err)
	}
	return nil
}

// readChunked removes RFC 9112 7.1's chunk framing and returns the content
// octets, never decoding one of them. Sizes, extensions and delimiters are
// framing: extensions are ignored, as 7.1.1 requires of a recipient that does not
// understand them. A trailer section is refused rather than dropped, because this
// instrument records every field that arrives and has nowhere to record these.
func readChunked(br *bufio.Reader) ([]byte, error) {
	var body bytes.Buffer
	for {
		line, err := readFramingLine(br)
		if err != nil {
			return nil, err
		}
		size, err := chunkSize(line)
		if err != nil {
			return nil, fmt.Errorf("%w: chunk-size line %q is not a chunk size (%w)",
				errInvalidFraming, line, err)
		}
		if size == 0 {
			break
		}
		if err = copyOctets(&body, br, size); err != nil {
			return nil, err
		}
		end, err := readFramingLine(br)
		if err != nil {
			return nil, err
		}
		if len(end) != 0 {
			return nil, fmt.Errorf("%w: a chunk of %d octet(s) is followed by %q rather "+
				"than the line ending that closes it", errInvalidFraming, size, end)
		}
	}
	trailer, err := readFramingLine(br)
	if err != nil {
		return nil, err
	}
	if len(trailer) != 0 {
		return nil, fmt.Errorf("%w: a trailer field (%q) -- this instrument records every "+
			"field that arrives and has nowhere to record a trailer, so it refuses rather "+
			"than dropping one", errUnimplemented, trailer)
	}
	return body.Bytes(), nil
}

// readFramingLine is readLine for a line inside a chunked body, where the
// connection ending is a truncated body rather than a quiet close.
func readFramingLine(br *bufio.Reader) ([]byte, error) {
	line, err := readLine(br)
	if errors.Is(err, io.EOF) {
		return nil, fmt.Errorf("reading chunk framing: %w", io.ErrUnexpectedEOF)
	}
	return line, err
}

// chunkSize reads 1*HEXDIG and ignores a chunk extension after it. Nothing wider:
// no sign, no space inside the digits, no empty size.
func chunkSize(line []byte) (int64, error) {
	digits := line
	if semi := bytes.IndexByte(line, ';'); semi >= 0 {
		digits = bytes.TrimRight(line[:semi], " \t")
	}
	if len(digits) == 0 {
		return 0, errors.New("empty")
	}
	for _, c := range digits {
		if !strings.ContainsRune("0123456789abcdefABCDEF", rune(c)) {
			return 0, fmt.Errorf("contains %q, which is not a hexadecimal digit", c)
		}
	}
	return strconv.ParseInt(string(digits), 16, 64)
}

// octetCount reads RFC 9110's Content-Length production and nothing wider: one
// or more decimal digits. strconv alone is too permissive here -- it accepts a
// sign, and a signed length parsed as a number is how `-5` became "no body".
func octetCount(v string) (int64, error) {
	if v == "" {
		return 0, errors.New("empty")
	}
	for i := 0; i < len(v); i++ {
		if v[i] < '0' || v[i] > '9' {
			return 0, fmt.Errorf("contains %q, which is not a decimal digit", v[i])
		}
	}
	// ParseInt, not ParseUint: the digit check above already refuses a sign, so
	// the value is non-negative by construction and this returns the width
	// io.CopyN takes -- which leaves no conversion for anyone to audit.
	return strconv.ParseInt(v, 10, 64)
}
