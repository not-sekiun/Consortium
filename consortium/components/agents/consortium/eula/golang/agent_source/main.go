package main

import (
	"eula/capabilities"
	"eula/core"
	"eula/info"
	"fmt"
)

func main() {
	// connection := core.NewConnection(
	// 	remoteHost,
	// 	remotePort,
	// 	sleepTime,
	// 	sleepTimeJitter,
	// 	agentType,
	// 	tasksUrlPaths,
	// 	resultsUrlPaths,
	// 	registrationUrlPaths,
	// 	extraHeaders,
	// )
	// connection.RegisterWithListener(map[string]string{"agentType": agentType})
	fmt.Println(info.GetSystemInfo())

	taskData := core.TaskData{}
	result := capabilities.Ls(taskData)
	fmt.Println(result)
}
