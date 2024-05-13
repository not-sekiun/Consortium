import os
import urllib.parse
import urllib.request


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

        if "output_filepath" in args:
            final_output_filepath = os.path.abspath(
                path_replace_sysenv_wrapper(args["output_filepath"], args["env_parse"]),
            )
        elif "output_dir" in args:
            final_output_filepath = os.path.abspath(
                path_replace_sysenv_wrapper(
                    os.path.join(
                        args["output_dir"],
                        os.path.basename(urllib.parse.urlparse(args["url"]).path),
                    ),
                    args["env_parse"],
                ),
            )
        else:
            final_output_filepath = os.path.abspath(
                os.path.join(
                    os.getcwd(),
                    os.path.basename(urllib.parse.urlparse(args["url"]).path),
                ),
            )

        path_already_exists = False
        if os.path.exists(final_output_filepath) and not args["overwrite"]:
            connection.send_string(
                f'[-]"{final_output_filepath}" already exists and overwriting is disabled, file not written to disk',
            )
            return
        elif os.path.exists(final_output_filepath):
            path_already_exists = True

        message = ""
        final_output_dir = os.path.dirname(final_output_filepath)
        if os.path.isfile(final_output_dir):
            os.remove(final_output_dir)
            os.mkdir(final_output_dir)
            message += f'[*] "{final_output_dir}" was originally a file but was deleted and automatically recreated as a directory\\n'
        elif not os.path.isdir(final_output_dir):
            os.mkdir(final_output_dir)
            message += f'[*] "{final_output_dir}" automatically created since it does not exist\\n'

        request_site = urllib.request.Request(
            args["url"],
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response = urllib.request.urlopen(request_site)

        with open(final_output_filepath, "wb") as f:
            while True:
                chunk = response.read(args["chunk_size"])
                if not chunk:
                    break
                f.write(chunk)

        if path_already_exists:
            message += f'[+] Downloaded (Overwritten) : (url) {args["url"]} -> (Remote) {final_output_filepath}'
        else:
            message += f'[+] Downloaded : (url) {args["url"]} -> (Remote) {final_output_filepath}'

        connection.send_string(message)
