package capabilities

import (
	"eula/core"
	"os"
)

func Ls(taskData core.TaskData) string {
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
