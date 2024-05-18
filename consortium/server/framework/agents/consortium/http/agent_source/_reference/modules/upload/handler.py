import argparse
import os
import zlib

from custom_exceptions.internal_peer_error_error import InternalPeerErrorError


class ModuleHandler:
    def __init__(self):
        self._examples = """
Examples:

    upload folder1 -r  # recursively upload all folders without -r only top level files and empty folders are uploaded
    upload file1 rel\\path\\file2 C:\\path\\to\\directory -d output_dir  # upload all files to directory output_dir without changing their names
    upload file1 -o

    upload file1 # verbose level 0 only displays file upload summary
    upload file1 -v  # verbose level 1 additionally displays error messages
    upload file1 -vv  # verbose level 2 additionally displays remote filepath being uploaded from
    upload file1 -vvv  # verbose level 3 additionally displays local filepath being uploaded to

"""
        self._parser = argparse.ArgumentParser(
            description="Upload files or directories to the remote host",
            prog="upload",
            epilog=self._examples,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self._parser.add_argument(
            "path",
            help="path of file or directory to upload",
            nargs="+",
        )

        self.group = self._parser.add_mutually_exclusive_group()
        self.group.add_argument(
            "-d",
            "--dirpath",
            help="Path of remote directory to upload files to, if directory does not exist, it is automatically created",
            nargs=1,
        )
        self._parser.add_argument(
            "-o",
            "--overwrite",
            help="flag to enable file overwriting. By default it is set to False. Without this flag, files will not be written if the filepath already exists on the local host",
            action="store_true",
        )
        self._parser.add_argument(
            "-v",
            "--verbosity",
            help="flag to set level of verbosity. A maximum of 3 layers of verbosity is possible",
            action="count",
        )
        self._parser.add_argument(
            "-r",
            "--recursive",
            help="flag to enable recursive directory upload. By default it is set to False. Without it only top level files are uploaded and empty directories copied",
            action="store_true",
        )
        self._parser.add_argument(
            "-c",
            "--chunk-size",
            help="size of chunk to read file in. By default 4096 (4 KB), if the chunk size is too large too much memory may be used on the remote host",
            type=int,
            default=4096,
        )
        self._parser.add_argument(
            "-z",
            "--zlib",
            help="level of zlib compression to apply to file chunks. By default set to 6 but it ranges from 0-9. Higher values use more memory, but are faster and produce smaller output. 0 indicates no compression",
            type=int,
            default=6,
        )
        self._parser.add_argument(
            "-e",
            "--envparse",
            help="flag to DISABLE parsing of environment variables in processing remote file/dir paths",
            action="store_false",
        )

    def _verbosity_print(
        self,
        verbosity_level,
        verbose_one=None,
        verbose_two=None,
        verbose_three=None,
    ):
        if not verbosity_level:
            pass
        elif verbosity_level == 1 and verbose_one:
            print(verbose_one)
        elif verbosity_level == 2 and verbose_two:
            print(verbose_two)
        elif verbosity_level == 3 and verbose_three:
            print(verbose_three)

    def _path_replace_sysenv_wrapper(self, filepath, process_sys_env_bool):
        if process_sys_env_bool:
            return self._path_replace_sysenv(filepath)
        else:
            return filepath

    def _path_replace_sysenv(self, filepath):
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

    def _walk_dirs_recursively(self, dir_path):
        root_abs_path = os.path.abspath(dir_path)
        for abs_root, dir_list, file_list in os.walk(root_abs_path):
            try:
                if file_list:
                    for file in file_list:
                        file_abs_path = os.path.join(abs_root, file)
                        yield (
                            True,
                            {
                                "is_file": True,
                                "abs_path": file_abs_path,
                                "rel_path": os.path.relpath(
                                    file_abs_path,
                                    os.path.split(root_abs_path)[0],
                                ),
                            },
                        )
                else:
                    yield (
                        True,
                        {
                            "is_file": False,
                            "abs_path": abs_root,
                            "rel_path": os.path.relpath(
                                abs_root,
                                os.path.split(root_abs_path)[0],
                            ),
                        },
                    )
            except PermissionError as e:
                yield False, e

    def _walk_dirs_non_recursively(self, dir_path):
        root_abs_path = os.path.abspath(dir_path)
        for item in os.listdir(root_abs_path):
            try:
                item_abs_path = os.path.join(root_abs_path, item)
                if os.path.isfile(item_abs_path):
                    yield (
                        True,
                        {
                            "is_file": True,
                            "abs_path": item_abs_path,
                            "rel_path": os.path.relpath(
                                item_abs_path,
                                os.path.split(root_abs_path)[0],
                            ),
                        },
                    )
                elif os.path.isdir(item_abs_path) and not os.listdir(item_abs_path):
                    yield (
                        True,
                        {
                            "is_file": False,
                            "abs_path": item_abs_path,
                            "rel_path": os.path.relpath(
                                item_abs_path,
                                os.path.split(root_abs_path)[0],
                            ),
                        },
                    )
            except PermissionError as e:
                yield False, e

    def _read_file_by_chunk(self, file_obj, chunk_size):
        while True:
            data = file_obj.read(chunk_size)
            if not data:
                break
            yield data

    def run_module(self, command, input_args, connection):
        try:
            parsed_args = self._parser.parse_args(input_args)
            successfully_uploaded_files = 0
            unsuccessfully_uploaded_files = 0
            empty_dirs_created = 0
            blocked_overwrites = 0

            if parsed_args.zlib not in range(0, 10):
                print("[-] Zlib compression value must be between 0-9")
            if parsed_args.chunk_size <= 0:
                print("[-] Chunk size must be greater than 0 bytes")
                return

            connection.send_json({"command": "upload", "args": []})

            for path in parsed_args.path:
                upload_path = self._path_replace_sysenv_wrapper(
                    path,
                    parsed_args.envparse,
                )

                print(f"[*] Uploading (Recursive : {parsed_args.recursive}) : {path}\n")

                if os.path.isfile(upload_path):

                    def get_downloadable_paths(requested_path):
                        file_abs_path = os.path.abspath(requested_path)
                        yield (
                            True,
                            {
                                "is_file": True,
                                "abs_path": file_abs_path,
                                "rel_path": os.path.split(file_abs_path)[1],
                            },
                        )
                elif os.path.isdir(upload_path) and parsed_args.recursive:
                    get_downloadable_paths = self._walk_dirs_recursively
                elif os.path.isdir(upload_path) and not parsed_args.recursive:
                    get_downloadable_paths = self._walk_dirs_non_recursively
                else:
                    print(f"[-] Invalid path : {upload_path}")
                    return

                for success_bool, file_info in get_downloadable_paths(upload_path):
                    if not success_bool:
                        print(f"[-] {file_info}")
                        continue

                    if file_info["is_file"]:
                        try:
                            with open(file_info["abs_path"], "rb") as f:
                                connection.send_json(
                                    {
                                        "is_file": True,
                                        "rel_path": file_info["rel_path"],
                                        "abs_path": file_info["abs_path"],
                                        "output_dir_path": parsed_args.dirpath,
                                        "file_size": os.path.getsize(
                                            os.path.abspath(file_info["abs_path"]),
                                        ),
                                        "overwrite": parsed_args.overwrite,
                                    },
                                )
                                _, response = connection.recv()
                                print(response)
                                # if success_bool and upload_confirmation['upload_status']:
                                #     for file_chunk in self._read_file_by_chunk(f, parsed_args.chunk_size):
                                #         compressed_chunk = zlib.compress(file_chunk, parsed_args.zlib)
                                #         scout_conn.send_bytes(compressed_chunk)
                                #     successfully_uploaded_files += 1
                                # else:
                                #     print(upload_confirmation['message'])
                        except InternalPeerErrorError as e:
                            unsuccessfully_uploaded_files += 1
                            print(
                                f"[-] Agent experienced an unexpected error : {str(e)}",
                            )
                        except Exception as e:
                            print(f"[-] Error reading file : {e}")
                    else:
                        connection.send_json(
                            {
                                "is_file": False,
                                "rel_path": file_info["rel_path"],
                                "abs_path": file_info["abs_path"],
                                "output_dir_path": parsed_args.dirpath,
                                "overwrite": parsed_args.overwrite,
                            },
                        )
                        _, response = connection.recv()
                        print(response)
                        # success_bool, upload_confirmation = scout_conn.recv_pyiris_message()
                        # if upload_confirmation['args']['upload_status']:
                        #     empty_dirs_created += 1
                        # else:
                        #     print(upload_confirmation['message'])

                connection.send_json({"upload_complete": True})
                print(f"[+] Completed upload of : {path}\n")

            print(f"[*] Upload summary : ")
            print(f" | [*] Number of files uploaded : {successfully_uploaded_files}")
            print(f" | [*] Number of empty directories created : {empty_dirs_created}")
            print(
                f" | [-] Number of files not uploaded due to error : {unsuccessfully_uploaded_files}",
            )
            print(
                f" | [-] Number of files / empty directories not uploaded due to potential overwrite : {blocked_overwrites}",
            )
        except SystemExit:
            pass
