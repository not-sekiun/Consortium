//go:build debug

package debug

import "log"

func LogErr(err error) {
	if err != nil {
		log.Printf("DEBUG ERROR: %v", err)
	}
}
