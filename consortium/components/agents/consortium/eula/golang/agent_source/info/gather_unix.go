//go:build linux || darwin

package info

import "os"

func IsAdmin() bool {
	return os.Geteuid() == 0
}

func GetLocale() string {
	lang := os.Getenv("LANG")
	if lang == "" {
		return ""
	}
	return lang
}
