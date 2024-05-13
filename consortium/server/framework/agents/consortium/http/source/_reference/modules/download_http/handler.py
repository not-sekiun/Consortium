import argparse

from custom_exceptions.internal_peer_error_error import InternalPeerErrorError


class ModuleHandler:
    def __init__(self):
        self._examples = """
Examples:

    download_http https://site.com/dir/file1  # Writes to current directory as file1
    download_http https://site.com/file1 https://site.com/file2 -f file1 ""  # Empty filenames specified with double quotes ("") will be files written with filename from url
    download_http https://site.com/file1 -f C:/output/file123  # Will not write to file123 if it alrady exists, "-o" will force file123 to be overwritten
    download_http https://site.com/dir1/dir2/file1 -f /output/filename -e  # -e disables environment variable parsing for local download path, directories such as %APPDATA% will be taken literally and not be resolved
    download_http https://site.com/file1 -o -d output\\directory  # Overwrites output\\directory\\file1

Note:
    The parser may sometimes erroneously parse and split URLs as if they were command line arguments. To circumvent this
    it is a "best practice" to encapsulate all URLs with double quotes.

"""
        self._parser = argparse.ArgumentParser(
            description="Download a file onto the remote host over HTTP/HTTPS from a URL",
            prog="download_http",
            epilog=self._examples,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self._parser.add_argument("url", help="url of file to download from", nargs="+")
        self.group = self._parser.add_mutually_exclusive_group()
        self.group.add_argument(
            "-f",
            "--filepath",
            help="Path of file to download to, if directory does not exist, it is automatically created",
            nargs="*",
        )
        self.group.add_argument(
            "-d",
            "--dirpath",
            help="Path of directory to download file to, if directory does not exist, it is automatically created",
            nargs=1,
        )
        self._parser.add_argument(
            "-o",
            "--overwrite",
            help="flag to enable file overwriting. By default it is set to False. Without this flag, files will not be written if the filepath already exists on the remote host",
            action="store_true",
        )
        self._parser.add_argument(
            "-e",
            "--envparse",
            help="flag to DISABLE parsing of environment variables in paths when changing writing to filepath or dirpath",
            action="store_false",
        )
        self._parser.add_argument(
            "-c",
            "--chunk-size",
            help="size of file chunk to read from when downloading files, by default 4096",
            default=4096,
            type=int,
        )

    def run_module(self, command, input_args, connection):
        try:
            parsed_args = self._parser.parse_args(input_args)
            if parsed_args.filepath:
                if len(parsed_args.url) == len(parsed_args.filepath):
                    for url, filepath in zip(parsed_args.url, parsed_args.filepath):
                        if filepath:
                            connection.send_json(
                                {
                                    "command": "download_http",
                                    "args": {
                                        "url": url,
                                        "output_filepath": filepath,
                                        "overwrite": parsed_args.overwrite,
                                        "env_parse": parsed_args.envparse,
                                        "chunk_size": parsed_args.chunk_size,
                                    },
                                },
                            )
                        else:
                            connection.send_json(
                                {
                                    "command": "download_http",
                                    "args": {
                                        "url": url,
                                        "overwrite": parsed_args.overwrite,
                                        "chunk_size": parsed_args.chunk_size,
                                    },
                                },
                            )
                        _, response = connection.recv()
                        print(response)
                else:
                    print(
                        f"[-] Number of output filepaths does not match number of URLs to download from",
                    )
            else:
                for url in parsed_args.url:
                    if parsed_args.dirpath:
                        connection.send_json(
                            {
                                "command": "download_http",
                                "args": {
                                    "url": url,
                                    "output_dir": parsed_args.dirpath[0],
                                    "overwrite": parsed_args.overwrite,
                                    "env_parse": parsed_args.envparse,
                                    "chunk_size": parsed_args.chunk_size,
                                },
                            },
                        )
                    else:
                        connection.send_json(
                            {
                                "command": "download_http",
                                "args": {
                                    "url": url,
                                    "overwrite": parsed_args.overwrite,
                                    "chunk_size": parsed_args.chunk_size,
                                },
                            },
                        )
                    _, response = connection.recv()
                    print(response)
        except SystemExit:
            pass
