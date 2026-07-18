package info

import (
	"eula/config"
	"net"
	"os"
	"os/user"
	"runtime"
)

type SystemInfo struct {
	AgentType        string `json:"agent_type"`
	User             string `json:"user"`
	IsAdmin          bool   `json:"is_admin"`
	OS               string `json:"os"`
	Version          string `json:"version"`
	Arch             string `json:"arch"`
	PID              int    `json:"pid"`
	Locale           string `json:"locale"`
	LocalIP string `json:"local_ip"`
	Hostname         string `json:"hostname"`
}

func getLocalIP() string {
	conn, err := net.Dial("udp", "10.255.255.255:1")
	if err != nil {
		return "127.0.0.1"
	}
	defer conn.Close()

	localAddr := conn.LocalAddr().(*net.UDPAddr)
	return localAddr.IP.String()
}

func getUser() string {
	currentUser, err := user.Current()
	if err != nil {
		return ""
	}
	return currentUser.Username
}

func getHostname() string {
	hostname, err := os.Hostname()
	if err != nil {
		return ""
	}
	return hostname
}

func GetSystemInfo() SystemInfo {
	return SystemInfo{
		AgentType:        config.AgentType,
		User:             getUser(),
		IsAdmin:          IsAdmin(),
		OS:               runtime.GOOS,
		Version:          GetVersion(),
		Arch:             runtime.GOARCH,
		PID:              os.Getpid(),
		Locale:           GetLocale(),
		LocalIP: getLocalIP(),
		Hostname:         getHostname(),
	}
}
