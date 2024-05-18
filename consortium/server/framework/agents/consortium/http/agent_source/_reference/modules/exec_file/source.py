import os
import subprocess
import sys


class ModuleSource:
    def __init__(self):
        pass

    def run_module(self, command, args, connection):
        def path_replace_sysenv_wrapper(filepath, process_sys_env_bool):
            if process_sys_env_bool:
                return path_replace_sysenv(filepath)
            else:
                return filepath

        def path_replace_sysenv(filepath):
            path = os.path.normpath(filepath)
            split_path = path.split(os.sep)
            for component_index, component in enumerate(split_path):
                if component.startswith("%") and component.endswith("%"):
                    env_var = component[1:-1]
                    if env_var in os.environ:
                        split_path[component_index] = os.environ[env_var]
                elif component.startswith('"%') and component.endswith('%"'):
                    split_path[component_index] = component[1:-1]
            return os.sep.join(split_path)

        exec_file_path = path_replace_sysenv_wrapper(
            args["filepath"],
            args["env_parse"],
        )

        if sys.platform == "win32":
            os.startfile(exec_file_path)
            connection.send_string(
                f'[+] Attempted to execute using "os.startfile()" function : {exec_file_path}',
            )
        elif sys.platform == "darwin":
            subprocess.call(["open", exec_file_path])
            connection.send_string(
                f'[+] Attempted to execute using "open" command : {exec_file_path}',
            )
        else:
            subprocess.call(["xdg-open", exec_file_path])
            connection.send_string(
                f'[+] Attempted to execute using "xdg-open" command : {exec_file_path}',
            )
