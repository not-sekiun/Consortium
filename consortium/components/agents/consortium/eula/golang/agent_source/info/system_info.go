package info

import (
	"eula/config"
	"runtime"
	"strconv"
)

func GetSystemInfo() map[string]string {
	return map[string]string{
		"agent_type": config.AgentType,
		"os":         runtime.GOOS,
		"arch":       runtime.GOARCH,
		"is_admin":   strconv.FormatBool(IsAdmin()),
	}
}
