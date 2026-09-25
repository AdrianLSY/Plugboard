package main

// How the origin answers a request it recorded: the reply chosen at startup,
// and the heads it writes. Split from main.go beside framing.go.

import (
	"errors"
	"fmt"
	"io"

	"plugboard/conformance/recorder"
)

// reply is how the origin answers a request it recorded.
type reply struct {
	// stated is the Content-Length the head declares; -1 means 204, which
	// declares none because RFC 9110 8.6 forbids one on that status.
	stated int
	// sent is how many of the stated octets are written before the close.
	sent int
}

// newReply turns the flags into a reply, refusing a combination that would
// answer something other than what was asked for.
func newReply(emitBytes, closeAfter int, emptyBody bool) (reply, error) {
	switch {
	case emitBytes < 0:
		return reply{}, fmt.Errorf("--emit-bytes %d is not a count of octets", emitBytes)
	case emptyBody && emitBytes > 0:
		return reply{}, errors.New("--empty-body states a length of zero and --emit-bytes states another")
	case closeAfter >= 0 && closeAfter >= emitBytes:
		return reply{}, fmt.Errorf("--close-after %d must be fewer octets than --emit-bytes %d "+
			"states, or the response is not truncated", closeAfter, emitBytes)
	case emptyBody:
		return reply{stated: 0, sent: 0}, nil
	case closeAfter >= 0:
		return reply{stated: emitBytes, sent: closeAfter}, nil
	case emitBytes > 0:
		return reply{stated: emitBytes, sent: emitBytes}, nil
	}
	return reply{stated: -1}, nil
}

// writeReply answers a recorded request as the origin was told to at startup.
// A truncated reply returns once its octets are written, and serve's deferred
// close is the close that truncates it.
func writeReply(w io.Writer, answer reply) error {
	if answer.stated < 0 {
		// No Content-Length: RFC 9110 8.6 forbids one in a 204, and a client
		// delimits a 204 at the end of its head.
		_, err := io.WriteString(w, "HTTP/1.1 204 No Content\r\nConnection: close\r\n\r\n")
		if err != nil {
			return fmt.Errorf("writing the status line: %w", err)
		}
		return nil
	}
	return writeHead(w, "200 OK", answer.stated, recorder.Pattern(answer.stated)[:answer.sent])
}

func writeStatus(w io.Writer, status string, body []byte) error {
	return writeHead(w, status, len(body), body)
}

// writeHead writes a head stating `stated` octets, then body. The two differ
// only for a truncated reply, which states more than it sends.
func writeHead(w io.Writer, status string, stated int, body []byte) error {
	head := fmt.Sprintf("HTTP/1.1 %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n",
		status, stated)
	if _, err := w.Write([]byte(head)); err != nil {
		return fmt.Errorf("writing the status line: %w", err)
	}
	if len(body) > 0 {
		if _, err := w.Write(body); err != nil {
			return fmt.Errorf("writing %d body octet(s): %w", len(body), err)
		}
	}
	return nil
}
