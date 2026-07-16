package core

type TaskData struct {
	taskID    string
	command   string
	arguments map[string]any
	data      any
}
