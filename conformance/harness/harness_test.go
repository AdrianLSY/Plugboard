//go:build integration

package harness_test

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"

	"plugboard/conformance/harness"
)

// The three process names these cases use. Named because they are the real
// chain's names, and because a typo in one would make a case assert about a
// process the harness was never given.
const (
	proxy  = "proxy"
	side   = "sidecar"
	origin = "recording-origin"
)

// The stub. One binary, three behaviours, so every case below exercises the same
// start path rather than a different one per case.
const stubSource = `package main

import (
	"flag"
	"os"
	"os/signal"
)

// block waits the way a server waits: on a signal. Not on a sleep -- a stub that
// slept would make every case here a race against a duration, and not on an
// empty select, which the runtime reports as a deadlock and exits on.
func block() {
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	<-c
}

func main() {
	ready := flag.String("ready-file", "", "")
	mode := flag.String("mode", "ready", "")
	flag.Parse()
	switch *mode {
	case "die":
		os.Stderr.WriteString("stub: refusing to start, on purpose\n")
		os.Exit(3)
	case "mute":
		block()
	}
	if err := os.WriteFile(*ready, []byte("127.0.0.1:65000\n"), 0o600); err != nil {
		os.Exit(1)
	}
	block()
}
`

func buildStub(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	write(t, filepath.Join(dir, "go.mod"), "module stub\n\ngo 1.27\n")
	write(t, filepath.Join(dir, "main.go"), stubSource)
	out := filepath.Join(dir, "stub")
	if runtime.GOOS == "windows" {
		out += ".exe"
	}
	cmd := exec.CommandContext(t.Context(), "go", "build", "-o", out, ".")
	cmd.Dir = dir
	if combined, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("building the stub: %v\n%s", err, combined)
	}
	return out
}

func write(t *testing.T, path, content string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
		t.Fatalf("writing %s: %v", path, err)
	}
}

// The property task 4.1 asks for: a process that exits non-zero is REPORTED BY
// NAME, and the harness does not hang waiting for it.
func TestAProcessThatExitsIsNamedRatherThanWaitedOn(t *testing.T) {
	stub := buildStub(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	started := time.Now()
	h, err := harness.Start(ctx, t.TempDir(), []harness.Spec{
		{Name: origin, Path: stub},
		{Name: side, Path: stub, Args: []string{"--mode", "die"}},
	})
	if h != nil {
		h.Stop()
	}
	if err == nil {
		t.Fatal("Start succeeded with a process that exited 3 -- the harness is " +
			"reporting a set of processes it does not have")
	}
	if !strings.Contains(err.Error(), side) {
		t.Errorf("the failure does not name the process that died: %v", err)
	}
	if !strings.Contains(err.Error(), "exit status 3") {
		t.Errorf("the failure does not carry the exit status: %v", err)
	}
	if !strings.Contains(err.Error(), "refusing to start") {
		t.Errorf("the failure does not carry the process's own output: %v", err)
	}
	// Not by deadline: it came back because the process exited.
	if elapsed := time.Since(started); elapsed > 20*time.Second {
		t.Errorf("Start took %v -- it waited out the deadline rather than "+
			"noticing the exit", elapsed)
	}
}

// A binary that does not exist yet is the state every gating test written before
// its subject is in, so the diagnostic for it is load-bearing rather than
// incidental.
func TestAnAbsentBinaryIsNamedWithItsPath(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	missing := filepath.Join(t.TempDir(), "proxy")

	h, err := harness.Start(ctx, t.TempDir(), []harness.Spec{
		{Name: proxy, Path: missing},
	})
	if h != nil {
		h.Stop()
	}
	if err == nil {
		t.Fatal("Start succeeded against a binary that does not exist")
	}
	for _, want := range []string{proxy, missing, "does not exist yet"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("the failure does not mention %q: %v", want, err)
		}
	}
}

// The control: three processes that do become ready start, and their addresses
// come back from the surface each wrote.
func TestReadyProcessesStartAndReportTheirAddresses(t *testing.T) {
	stub := buildStub(t)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	h, err := harness.Start(ctx, t.TempDir(), []harness.Spec{
		{Name: proxy, Path: stub},
		{Name: side, Path: stub},
		{Name: origin, Path: stub},
	})
	if err != nil {
		t.Fatalf("Start: %v", err)
	}
	defer h.Stop()
	for _, name := range []string{proxy, side, origin} {
		addr, err := h.Address(name)
		if err != nil {
			t.Errorf("%s: %v", name, err)
			continue
		}
		if addr != "127.0.0.1:65000" {
			t.Errorf("%s: address %q, want what the process wrote", name, addr)
		}
	}
}

// A process that starts, says nothing and never becomes ready is reported
// against its readiness surface rather than left to hang.
func TestAProcessThatNeverBecomesReadyIsNamed(t *testing.T) {
	stub := buildStub(t)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	h, err := harness.Start(ctx, t.TempDir(), []harness.Spec{
		{Name: "terminator", Path: stub, Args: []string{"--mode", "mute"}},
	})
	if h != nil {
		h.Stop()
	}
	if err == nil {
		t.Fatal("Start succeeded against a process that never wrote its readiness file")
	}
	for _, want := range []string{"terminator", "never wrote its readiness file"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("the failure does not mention %q: %v", want, err)
		}
	}
}
