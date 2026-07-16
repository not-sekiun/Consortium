package core

import (
	"strconv"
)

type Connection struct {
	remoteHost               string
	remotePort               int
	sleepTime                float64
	sleepTimeJitter          float64
	agentType                string
	tasksUrlPathsJson        []string
	resultsUrlPathsJson      []string
	registrationUrlPathsJson []string
	extraHeadersJson         map[string]string
	listenerBaseUrl          string
	agentID                  *string
}

func NewConnection(
	remoteHost string,
	remotePort int,
	sleepTime float64,
	sleepTimeJitter float64,
	agentType string,
	tasksUrlPathsJson []string,
	resultsUrlPathsJson []string,
	registrationUrlPathsJson []string,
	extraHeadersJson map[string]string,
) *Connection {
	return &Connection{
		remoteHost:               remoteHost,
		remotePort:               remotePort,
		sleepTime:                sleepTime,
		sleepTimeJitter:          sleepTimeJitter,
		agentType:                agentType,
		tasksUrlPathsJson:        tasksUrlPathsJson,
		resultsUrlPathsJson:      resultsUrlPathsJson,
		registrationUrlPathsJson: registrationUrlPathsJson,
		extraHeadersJson:         extraHeadersJson,
		listenerBaseUrl:          "http://" + remoteHost + ":" + strconv.Itoa(remotePort),
		agentID:                  nil,
	}
}
