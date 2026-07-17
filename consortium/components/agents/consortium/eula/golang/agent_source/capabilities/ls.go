package capabilities

import (
	"eula/connection"
	"os"
)

func Ls(taskData connection.TaskData) string {
	entries, err := os.ReadDir(".")
	if err != nil {
		panic(err)
	}
	result := ""
	for _, entry := range entries {
		result += entry.Name() + "\n"
	}
	return result
}
