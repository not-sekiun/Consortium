package info

import (
	"eula/config"
	"os"
	"runtime"
	"strconv"
)

func GetSystemInfo() map[string]string {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = ""
	}

	return map[string]string{
		"agent_type": config.AgentType,
		"os":         runtime.GOOS,
		"arch":       runtime.GOARCH,
		"is_admin":   strconv.FormatBool(IsAdmin()),
		"hostname":   hostname,
		"locale":     GetLocale(),
	}
}
