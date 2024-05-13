import argparse
import os
import shutil
import zlib
from threading import local

from custom_exceptions.internal_peer_error_error import InternalPeerErrorError


class ModuleHandler:
    def __init__(self):
        self._examples = """
Examples:

    download folder1 -r  # recursively download all folders without -r only top level files and empty folders are downloaded
    download file1 rel\\path\\file2 C:\\path\\to\\directory -d output_dir  # download all files to directory output_dir without changing their names
    download file1 -o

    download file1 # verbose level 0 only displays file download summary
    download file1 -v  # verbose level 1 additionally displays error messages
    download file1 -vv  # verbose level 2 additionally displays remote filepath being downloaded from
    download file1 -vvv  # verbose level 3 additionally displays local filepath being downloaded to

"""
        self._parser = argparse.ArgumentParser(
            description="Download files or directories from the remote host",
            prog="download",
            epilog=self._examples,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self._parser.add_argument(
            "path",
            help="path of file or directory to download from remote host",
            nargs="+",
        )

        self.group = self._parser.add_mutually_exclusive_group()
        self.group.add_argument(
            "-d",
            "--dirpath",
            help="Path of local directory to download files to, if directory does not exist, it is automatically created",
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
            help="flag to enable recursive directory download. By default it is set to False. Without it only top level files are downloaded and empty directories copied",
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
            type=int,
            default=6,
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

    def run_module(self, command, input_args, connection):
        try:
            parsed_args = self._parser.parse_args(input_args)
            successfully_downloaded_files = 0
            unsuccessfully_downloaded_files = 0
            empty_dirs_created = 0
            blocked_overwrites = 0

            if parsed_args.zlib not in range(0, 10):
                print("[-] Zlib compression value must be between 0-9")
                return
            if parsed_args.chunk_size <= 0:
                print("[-] Chunk size must be greater than 0 bytes")
                return

            for path in parsed_args.path:
                print(
                    f"[*] Downloading (Recursive : {parsed_args.recursive}) : {path}\n",
                )

                connection.send_json(
                    {
                        "command": "download",
                        "args": {
                            "path": path,
                            "recursive": parsed_args.recursive,
                            "chunk_size": parsed_args.chunk_size,
                            "zlib_compression": parsed_args.zlib,
                            "env_parse": parsed_args.envparse,
                        },
                    },
                )
                while True:
                    try:
                        _, response = connection.recv()
                        if "valid_path_error" in response:
                            print(response["message"])
                            break
                        elif "download_complete" in response:
                            break
                        elif "read_file_error" in response:
                            unsuccessfully_downloaded_files += 1
                            print(response["message"])
                        else:
                            remote_path = response["abs_path"]
                            if parsed_args.dirpath:
                                local_path = os.path.abspath(
                                    os.path.join(
                                        parsed_args.dirpath[0],
                                        response["rel_path"],
                                    ),
                                )
                            else:
                                local_path = os.path.abspath(response["rel_path"])

                            if parsed_args.dirpath:
                                if not os.path.exists(parsed_args.dirpath[0]):
                                    os.mkdir(parsed_args.dirpath[0])
                                    print(
                                        f"[*] Created user specified non existent directory locally {parsed_args.dirpath[0]}",
                                    )

                            if os.path.exists(local_path) and not parsed_args.overwrite:
                                if response["is_file"]:
                                    print(
                                        f'[-] "{local_path}" (Local) already exists and overwriting is disabled, file "{remote_path}" (Remote) not downloaded',
                                    )
                                    connection.send_string("False")
                                else:
                                    print(
                                        f'[-] "{local_path}" (Local) already exists and overwriting is disabled, directory "{remote_path}" (Remote) not copied',
                                    )
                                blocked_overwrites += 1
                            else:
                                path_exists_before_write = os.path.exists(local_path)
                                if response["is_file"]:
                                    connection.send_string("True")

                                    if not os.path.isdir(os.path.dirname(local_path)):
                                        os.makedirs(os.path.dirname(local_path))
                                    elif path_exists_before_write:
                                        if os.path.isdir(local_path):
                                            shutil.rmtree(local_path)
                                    with open(local_path, "wb") as f:
                                        written_len = 0
                                        while written_len != response["file_size"]:
                                            _, compressed_file_data = connection.recv()
                                            file_data = zlib.decompress(
                                                compressed_file_data,
                                            )
                                            written_len += len(file_data)
                                            f.write(file_data)

                                    successfully_downloaded_files += 1

                                    if path_exists_before_write:
                                        verbose_one_msg = f"[+] Downloaded file (Local file was overwritten!) : (Remote) {remote_path}"
                                        self._verbosity_print(
                                            parsed_args.verbosity,
                                            verbose_two=verbose_one_msg,
                                            verbose_three=verbose_one_msg
                                            + f" -> (Local) {local_path}",
                                        )
                                    else:
                                        verbose_one_msg = f"[+] Downloaded file : (Remote) {remote_path}"
                                        self._verbosity_print(
                                            parsed_args.verbosity,
                                            verbose_two=verbose_one_msg,
                                            verbose_three=verbose_one_msg
                                            + f" -> (Local) {local_path}",
                                        )
                                else:
                                    if path_exists_before_write:
                                        verbose_one_msg = f"[-] Created empty directory (Local dir was overwritten!) : (Remote) {remote_path}"
                                        self._verbosity_print(
                                            parsed_args.verbosity,
                                            verbose_two=verbose_one_msg,
                                            verbose_three=verbose_one_msg
                                            + f" -> (Local) {local_path}",
                                        )
                                    else:
                                        os.makedirs(os.path.join(path, local_path))
                                        empty_dirs_created += 1

                                        verbose_one_msg = f"[+] Created empty directory : (Remote) {remote_path}"
                                        self._verbosity_print(
                                            parsed_args.verbosity,
                                            verbose_two=verbose_one_msg,
                                            verbose_three=verbose_one_msg
                                            + f" -> (Local) {local_path}",
                                        )
                    except InternalPeerErrorError as e:
                        print(f"[-] Agent experienced an unexpected error : {str(e)}")
                        unsuccessfully_downloaded_files += 1
                    except (
                        PermissionError,
                        IsADirectoryError,
                    ) as e:  # Catch error when trying to write a file to a path that has an existing directory. PermissionError raised on Windows, IsADirectoryError raised on linux
                        print(
                            "[-] Error experienced locally while downloading file : {e}",
                        )
                print(f"[+] Completed download of : {path}\n")

            print(f"[*] Download summary : ")
            print(
                f" | [*] Number of files downloaded : {successfully_downloaded_files}",
            )
            print(f" | [*] Number of empty directories created : {empty_dirs_created}")
            print(
                f" | [-] Number of files not downloaded due to error : {unsuccessfully_downloaded_files}",
            )
            print(
                f" | [-] Number of files / empty directories not downloaded due to potential overwrite : {blocked_overwrites}",
            )
        except SystemExit:
            pass
