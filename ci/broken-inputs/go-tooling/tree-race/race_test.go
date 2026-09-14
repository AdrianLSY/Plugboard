package violating

import (
	"sync"
	"testing"
)

// Two goroutines writing one variable with no synchronisation. -race is not a
// flag a contributor is asked to remember -- ci/make/go.mk makes it the
// invocation -- and a data race in a proxy is a corrupted response body, the
// defect class least likely to reproduce under a rerun.
func TestRace(t *testing.T) {
	shared := 0
	var wg sync.WaitGroup
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			shared++
		}()
	}
	wg.Wait()
	_ = shared
}
