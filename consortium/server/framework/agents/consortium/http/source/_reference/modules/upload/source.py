import os
import zlib


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

        while True:
            _, file_info = connection.recv()

            if "upload_complete" in file_info:
                break

            if file_info["output_dir_path"]:
                output_path = os.path.join(
                    file_info["output_dir_path"],
                    file_info["rel_path"],
                )
            else:
                output_path = file_info["rel_path"]

            # if os.path.exists(output_path) and not file_info['overwrite']:
            #     connection.send_json({'upload_file_success': False,
            #                           'message': f' | [-] "{output_path}" already exists on the remote host and overwriting is not enabled. Skipping upload...'})
            # elif os.path.isdir(output_path) and not file_info['overwrite']:
            #     connection.send_json({'upload_file_success': False,
            #                           'message': f' | [-] File path {output_path} already exists on the remote host and overwriting is not enabled. Skipping upload...'})
            # elif os.path.isfile(output_path) and file_info['overwrite']:
            #     connection.send_json({'upload_file_success': True,
            #                           'message': f' | [+] Uploaded file (Remote file was overwritten!) : (Remote) {output_path}'})
            # elif os.path.isdir(output_path) and file_info['overwrite'] and file_info['is_file']:
            #     connection.send_json({'upload_file_success': True,
            #                           'message': f''})
            # elif file_info['is_file']:
            #     connection.send_json({'upload_file_success': True,
            #                           'message': f''})
            # elif not file_info['is_file']:
            #     connection.send_json({'upload_file_success': True,
            #                           'message': f''})

            connection.send_json({"file_info": file_info, "output_path": output_path})
