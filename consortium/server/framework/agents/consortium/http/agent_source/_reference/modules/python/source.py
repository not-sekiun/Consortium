import io
import sys
import traceback


class ModuleSource:
    def __init__(self):
        self._pseudo_global_namespace = {}

    def run_module(self, command, args, connection):
        if args["reset"]:
            self._pseudo_global_namespace = {}
            self._pseudo_local_namespace = {}
            connection.send_string("[+] Reset namespace")
        elif args["interactive"]:
            old_stdout = sys.stdout
            result = io.StringIO()
            sys.stdout = result
            try:
                exec(args["interactive"], self._pseudo_global_namespace)
            except Exception:
                result.write(traceback.format_exc())
            sys.stdout = old_stdout
            output = result.getvalue()
            connection.send_string(output)
        elif args["expressions"] or args["files"]:
            for _, v in args.items():
                if v:
                    old_stdout = sys.stdout
                    result = io.StringIO()
                    sys.stdout = result
                    for execute in v:
                        try:
                            exec(execute, self._pseudo_global_namespace)
                        except Exception:
                            result.write(traceback.format_exc())
                    sys.stdout = old_stdout
                    output = result.getvalue()
                    connection.send_string(output)
                    break
