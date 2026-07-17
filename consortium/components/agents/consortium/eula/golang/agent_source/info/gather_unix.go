//go:build linux || darwin

package info

import (
	"os"
	"strings"
)

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

func GetVersion() string {
	data, err := os.ReadFile("/etc/os-release")
	if err != nil {
		return ""
	}
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, "PRETTY_NAME=") {
			return strings.TrimPrefix(line, "PRETTY_NAME=")
		}
	}
	return ""
}
