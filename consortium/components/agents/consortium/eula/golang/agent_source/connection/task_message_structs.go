package connection

import (
	"json"
)

type TaskData struct {
	Command   string
	Arguments map[string]any
	Data      any
}

type taskLaunchMessage struct {
	TaskID    string         `json:"task_id"`
	Command   string         `json:"command"`
	Arguments map[string]any `json:"arguments"`
	Data      any            `json:"data"`
}

type taskInputMessage struct {
	TaskID string `json:"task_id"`
	Data   any    `json:"data"`
}

type taskOutputMessage struct {
	TaskID  string `json:"task_id"`
	Success bool   `json:"success"`
	Message string `json:"message"`
	Data    any    `json:"data"`
}

type TaskMessage struct {
	TaskID    string          `json:"task_id"`
	Command   string          `json:"command,omitempty"`
	Arguments json.RawMessage `json:"arguments,omitempty"`
	Data      json.RawMessage `json:"data"`
}
