import asyncio
import json
import socket
import struct
from typing import Any

from consortium.components.listeners.consortium.reverse_tcp.listener_type import (
    LISTENER_TYPE,
)
from consortium.framework.exceptions.listeners_framework_exceptions import (
    ListenerStartError,
)
from consortium.framework.listeners.base_listener import BaseListener


class _AgentHandler:
    def __init__(
        self,
        agents_manager: "AgentsManager",
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        self._agents_manager = agents_manager
        self._reader = reader
        self._writer = writer

        self._agent_result_schema = {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "task_id": {"type": "string"},
                "result": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "data": {"type": "object"},
                    },
                    "required": ["success", "message", "data"],
                },
            },
            "required": ["agent_id", "task_id", "result"],
        }

    async def _send_message(self, message: dict[str, Any]) -> None:
        message_bytes = json.dumps(message).encode()
        if len(message_bytes) > 2**32:
            assert False, (
                "The message to be sent is too large to be sent over the reverse TCP "
                "transport.",
            )
        message_header = struct.pack(">I", len(message_bytes))
        self._writer.write(message_header + message_bytes)

    async def _recv_message(self) -> dict[str, Any]:
        message_header = b""
        while len(message_header) < 4:
            # The call to `read()` reads at most 4 bytes, but may read less.
            message_header += await self._reader.read(4)
        message_length = struct.unpack(">I", message_header)[0]
        message = b""
        while len(message) < message_length:
            message += await self._reader.read(1024 * 1024)
        # TODO: Add error handling malformed messages.
        return json.loads(message)

    async def run_agent_handler(self) -> None:
        pass
        # try:
        #     initial_check_in_agent_data = await self._recv_message()
        #     self._agents_manager.register_new_connected_agent(
        #         agent_type=AGENT_TYPE,  # TODO: Change to the reverse TCP agent type later.
        #     )
        #     while True:
        #         agent_result = await self._recv_message()
        #         jsonschema.validate(agent_result, self._agent_result_schema)
        #         await self._send_message(agent_result)
        # except (json.JSONDecodeError, jsonschema.ValidationError):
        #     self._writer.close()
        #     await self._writer.wait_closed()
        #     return


class Listener(BaseListener):
    listener_type = LISTENER_TYPE

    async def on_listener_started(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]

        try:
            test_socket = socket.socket()
            test_socket.bind((local_host, local_port))
            test_socket.close()
        except socket.error as exc:
            raise ListenerStartError(
                f"An error occurred while attempting to start the listener. Listener "
                f"was unable to bind to the provided host and port due to the "
                f"following socket error: {exc}",
            )

    async def on_listener_running(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]

        async def handle_agent(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
        ) -> None:
            agent_handler = _AgentHandler(
                agents_manager=self.agents_manager,
                reader=reader,
                writer=writer,
            )
            await agent_handler.run_agent_handler()

        await asyncio.start_server(
            client_connected_cb=handle_agent,
            host=local_host,
            port=local_port,
        )

        await self.stop_listener_event.wait()

    async def on_listener_stopped(self) -> None:
        pass

    async def on_listener_cancelled(self) -> None:
        pass

    async def on_listener_errored(self, exception: Exception) -> None:
        self.listener_logger.error(exception)
