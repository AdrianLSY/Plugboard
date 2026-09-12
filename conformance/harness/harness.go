// Package harness starts the processes an end-to-end case needs, waits on their
// readiness surfaces and on nothing else, and tears them down.
//
// The two properties that make it a harness rather than a script:
//
//   - IT NEVER SLEEPS. Readiness is a file the process writes once it is
//     listening. A harness that sleeps is a harness that hides a process which
//     never started, and then the suite's failures are about timing.
//   - A PROCESS THAT DIES IS NAMED. If a process exits before it is ready, Start
//     returns saying which one and what it exited with. The prior attempt's wait
//     helper called a reload entry point on timeout and reported success, so 947
//     lines of tests passed while the mechanism under test had never run.
//
// It also never repairs what it waits for: no restart, no resync, no retry that
// changes the state being observed. See
// docs/code/rules/no-helper-repairing-awaited-state.md.
package harness

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// Spec describes one process to start.
type Spec struct {
	// Name is what a failure calls it.
	Name string
	// Path is the executable. A missing one is reported as a missing binary for
	// THIS process, which is the diagnostic a gating test written before its
	// subject exists depends on.
	Path string
	Args []string
	Env  []string
}

// readyPollInterval is how often the readiness file is looked for. It is a poll
// of a surface the process owns, never a wait for time to pass: the deadline
// below is a backstop against a hang, not the mechanism.
const readyPollInterval = 5 * time.Millisecond

// Field order here and in the two structs below is govet fieldalignment's, not a
// reader's. The linter is on because task 2.3 asked for `enable-all`; the trade
// is recorded in docs/method/follow-ups.md with the count, so keeping or
// dropping it later is a decision on evidence rather than on irritation.
type proc struct {
	cmd       *exec.Cmd
	output    *syncBuffer
	exited    chan error
	readyFile string
	spec      Spec
}

// Harness is a started set of processes.
type Harness struct {
	dir   string
	procs []*proc
}

// Start launches every spec and returns once all of them are ready, or as soon
// as any one of them fails -- whichever happens first. dir holds each process's
// readiness file and is the caller's to keep or discard.
//
// Each spec is given a `--ready-file` argument pointing into dir. A process that
// does not take one is not startable by this harness, on purpose: a readiness
// surface is a requirement of being started here, not an optional extra.
func Start(ctx context.Context, dir string, specs []Spec) (*Harness, error) {
	h := &Harness{dir: dir}
	for _, spec := range specs {
		p, err := h.launch(ctx, spec)
		if err != nil {
			h.Stop()
			return nil, err
		}
		h.procs = append(h.procs, p)
	}
	for _, p := range h.procs {
		if err := waitReady(ctx, p); err != nil {
			h.Stop()
			return nil, err
		}
	}
	return h, nil
}

func (h *Harness) launch(ctx context.Context, spec Spec) (*proc, error) {
	if _, err := os.Stat(spec.Path); err != nil {
		return nil, fmt.Errorf(
			"%s: no binary at %s -- this process does not exist yet, so nothing "+
				"downstream of it ran. That is the finding; an assertion that "+
				"passed here would be an assertion about an empty exchange",
			spec.Name, spec.Path)
	}
	readyFile := filepath.Join(h.dir, spec.Name+".ready")
	out := &syncBuffer{}
	//nolint:gosec // G204: starting a declared binary IS this package's purpose. The
	// path comes from a Spec written in a test, never from a request or a file.
	cmd := exec.CommandContext(ctx, spec.Path, append(append([]string(nil), spec.Args...),
		"--ready-file", readyFile)...)
	cmd.Env = append(os.Environ(), spec.Env...)
	cmd.Stdout = out
	cmd.Stderr = out
	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("%s: could not start %s: %w", spec.Name, spec.Path, err)
	}
	p := &proc{spec: spec, cmd: cmd, readyFile: readyFile, output: out,
		exited: make(chan error, 1)}
	go func() { p.exited <- cmd.Wait() }()
	return p, nil
}

// waitReady blocks until the process writes its readiness file, exits, or the
// context is done. Those three and nothing else.
func waitReady(ctx context.Context, p *proc) error {
	ticker := time.NewTicker(readyPollInterval)
	defer ticker.Stop()
	for {
		if _, err := os.Stat(p.readyFile); err == nil {
			return nil
		}
		select {
		case err := <-p.exited:
			return fmt.Errorf(
				"%s: exited before it was ready (%v). Its output was:\n%s",
				p.spec.Name, describeExit(err), p.output.String())
		case <-ctx.Done():
			return fmt.Errorf(
				"%s: never wrote its readiness file %s, and the deadline passed. "+
					"Its output was:\n%s", p.spec.Name, p.readyFile, p.output.String())
		case <-ticker.C:
		}
	}
}

func describeExit(err error) string {
	if err == nil {
		return "exit status 0"
	}
	var exit *exec.ExitError
	if errors.As(err, &exit) {
		return fmt.Sprintf("exit status %d", exit.ExitCode())
	}
	return err.Error()
}

// Address returns what the named process wrote into its readiness file, which is
// the address it bound.
func (h *Harness) Address(name string) (string, error) {
	for _, p := range h.procs {
		if p.spec.Name != name {
			continue
		}
		b, err := os.ReadFile(p.readyFile)
		if err != nil {
			return "", fmt.Errorf("%s: reading its readiness file: %w", name, err)
		}
		return strings.TrimSpace(string(b)), nil
	}
	return "", fmt.Errorf("%s: no such process in this harness", name)
}

// Output returns everything the named process wrote to stdout and stderr.
func (h *Harness) Output(name string) string {
	for _, p := range h.procs {
		if p.spec.Name == name {
			return p.output.String()
		}
	}
	return ""
}

// Stop tears every process down. It is safe to call more than once.
func (h *Harness) Stop() {
	for _, p := range h.procs {
		if p.cmd.Process != nil {
			_ = p.cmd.Process.Kill() //nolint:errcheck // a process that is already gone is the outcome wanted
		}
	}
	h.procs = nil
}

type syncBuffer struct {
	buf []byte
	mu  sync.Mutex
}

func (s *syncBuffer) Write(b []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.buf = append(s.buf, b...)
	return len(b), nil
}

func (s *syncBuffer) String() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return string(s.buf)
}
