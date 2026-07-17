package info

import (
	"eula/config"
	"net"
	"os"
	"os/user"
	"runtime"
	"strconv"
)

func getLocalHostAddress() string {
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

func GetSystemInfo() map[string]string {
	return map[string]string{
		"agent_type":         config.AgentType,
		"user":               getUser(),
		"is_admin":           strconv.FormatBool(IsAdmin()),
		"os":                 runtime.GOOS,
		"version":            GetVersion(),
		"arch":               runtime.GOARCH,
		"pid":                strconv.Itoa(os.Getpid()),
		"locale":             GetLocale(),
		"local_host_address": getLocalHostAddress(),
		"hostname":           getHostname(),
	}
}
