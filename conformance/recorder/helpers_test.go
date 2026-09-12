package recorder_test

import (
	"os"
	"path/filepath"
)

func readFile(dir, name string) ([]byte, error) {
	return os.ReadFile(filepath.Join(dir, name))
}
