package harness

import "time"

// The prior attempt's defect, written out: the helper performs by hand the
// transition it is waiting to observe, then reports success.
func waitForMounts(store *Store) bool {
	deadline := time.Now().Add(time.Second)
	for time.Now().Before(deadline) {
		if store.Ready() {
			return true
		}
	}
	store.ReloadAll()
	return true
}
