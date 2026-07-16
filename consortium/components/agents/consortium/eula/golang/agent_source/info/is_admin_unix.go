//go:build linux || darwin

package info

import "os"

func IsAdmin() bool {
	return os.Geteuid() == 0
}
