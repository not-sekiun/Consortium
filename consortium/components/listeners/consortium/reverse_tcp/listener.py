import asyncio
import json
import socket
import struct
import uuid
from typing import Any

import jsonschema
from pydantic import ValidationError

from consortium.framework.exceptions import ListenerStartError
from consortium.framework.listeners import BaseListener
from consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions import (
    AgentTypeResolutionError,
)


class _AgentHandler:
    def __init__(
        self,
        logger,
        connected_agents_service,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        stop_event: asyncio.Event,
    ):
        self._logger = logger
        self._connected_agents_service = connected_agents_service
        self._reader = reader
        self._writer = writer
        self._stop_event = stop_event

    async def _send_message(self, message: dict[str, Any]) -> None:
        message_bytes = json.dumps(message).encode()
        if len(message_bytes) > 2**32:
            raise ValueError(
                "The message to be sent is too large to be sent over the reverse TCP "
                "transport.",
            )
        header = struct.pack(">I", len(message_bytes))
        self._writer.write(header + message_bytes)
        await self._writer.drain()

    async def _recv_message(self) -> bytes:
        header = await self._reader.readexactly(4)
        message_length = struct.unpack(">I", header)[0]
        return await self._reader.readexactly(message_length)

    async def _close_connection(self) -> None:
        self._writer.close()
        await self._writer.wait_closed()

    @staticmethod
    def _decode_message_as_json(message: bytes) -> dict[str, Any]:
        return json.loads(message.decode())

    @staticmethod
    def _construct_agent_result_message_from_json(
        agent_result_json: dict[str, Any],
    ) -> Any:
        raise NotImplementedError

    @staticmethod
    def _construct_agent_result_message_from_binary(
        agent_result_json: dict[str, Any],
    ) -> Any:
        raise NotImplementedError

    async def _handle_send_tasks_to_agent(self, agent_id: uuid.UUID) -> None:
        self._logger.warning(
            "Sending tasks to agent {} is not yet implemented.", agent_id
        )
        await self._close_connection()

    async def _handle_recv_tasks_from_agent(self, agent_id: uuid.UUID) -> None:
        self._logger.warning(
            "Receiving tasks from agent {} is not yet implemented.", agent_id
        )
        await self._close_connection()

        # message_payload_json_schema = {
        #     "type": "object",
        #     "properties": {
        #         "success": {"type": "boolean"},
        #         "message": {"type": "string"},
        #         "data": {"type": "object"},
        #     },
        #     "required": ["success", "message", "data"],
        #     "additionalProperties": False,
        # }
        # binary_header_payload_json_schema = {
        #     "type": "object",
        #     "properties": {
        #         "is_last_chunk": {"type": "boolean"},
        #     },
        #     "required": ["is_last_chunk"],
        #     "additionalProperties": False,
        # }
        # agent_result_json_schema = {
        #     "type": "object",
        #     "properties": {
        #         "agent_id": {"type": "string"},
        #         "task_id": {"type": "string"},
        #         "type": {"type": "string", "enum": ["message", "binary"]},
        #         "payload": {
        #             "type": "object",
        #             "oneOf": [
        #                 message_payload_json_schema,
        #                 binary_header_payload_json_schema,
        #             ],
        #         },
        #     },
        #     "required": ["agent_id", "task_id", "type", "payload"],
        #     "additionalProperties": False,
        # }
        #
        # while not self._stop_event.is_set():
        #     # Receive and validate agent result message
        #     try:
        #         agent_result_message = self._decode_message_as_json(
        #             await self._recv_message()
        #         )
        #         jsonschema.validate(
        #             agent_result_message,
        #             agent_result_json_schema,
        #         )
        #         if agent_result_message["type"] == "message":
        #             jsonschema.validate(
        #                 agent_result_message["payload"],
        #                 message_payload_json_schema,
        #             )
        #         else:
        #             jsonschema.validate(
        #                 agent_result_message["payload"],
        #                 binary_header_payload_json_schema,
        #             )
        #     except (jsonschema.ValidationError, ValidationError):
        #         self._logger.warning(
        #             "Received an invalid agent result message from agent {}. "
        #             "Closing connection.",
        #             agent_id,
        #         )
        #         await self._close_connection()
        #         return
        #
        #     # Process agent result message
        #     if agent_result_message["type"] == "message":
        #         agent_result = self._construct_agent_result_message_from_json(
        #             agent_result_json=agent_result_message,
        #         )
        #     else:
        #         agent_result = self._construct_agent_result_message_from_binary(
        #             agent_result_json=agent_result_message,
        #         )

    async def run_agent_handler(self) -> None:
        agent_registration_json_schema = {
            "type": "object",
            "properties": {
                "payload_id": {"type": "string"},
                "agent_type": {"type": "string"},
                "is_admin": {"type": "boolean"},
                "os": {"type": "string"},
                "version": {"type": "string"},
                "arch": {"type": "string"},
                "pid": {"type": "integer"},
                "locale": {"type": "string"},
                "local_host_address": {"type": "string"},
                "hostname": {"type": "string"},
            },
            "oneOf": [{"required": ["payload_id"]}, {"required": ["agent_type"]}],
            "additionalProperties": False,
        }

        # Receive and validate agent registration message
        try:
            agent_registration_message = self._decode_message_as_json(
                await self._recv_message()
            )
            jsonschema.validate(
                agent_registration_message,
                agent_registration_json_schema,
            )
        except (jsonschema.ValidationError, ValidationError):
            await self._close_connection()
            return

        # Register agent to framework
        payload_id = agent_registration_message.pop("payload_id", None)
        agent_type = agent_registration_message.pop("agent_type", None)
        try:
            agent = self._connected_agents_service.register_agent(
                payload_id=payload_id,
                agent_type=agent_type,
                **agent_registration_message,
            )
        except AgentTypeResolutionError:
            if agent_type:
                self._logger.warning(
                    "Agent attempted to register with an invalid agent type: {}. "
                    "Closed connection.",
                    agent_type,
                )
            else:
                self._logger.warning(
                    "Agent attempted to register with an invalid payload ID: {}. "
                    "Closed connection.",
                    payload_id,
                )
            await self._close_connection()
            return

        # Start sending tasks and receiving results to and from the agent
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(
                    self._handle_send_tasks_to_agent(agent_id=agent.agent_id)
                )
                tg.create_task(
                    self._handle_recv_tasks_from_agent(agent_id=agent.agent_id)
                )
        except Exception as exc:
            self._logger.error(
                "Closing agent connection due to an error occurring while handling the "
                "agent {}: {}",
                agent,
                str(exc),
            )
        finally:
            await self._close_connection()
            self._connected_agents_service.deregister_agent_by_agent_id(
                agent_id=agent.agent_id,
            )


class Listener(BaseListener):
    async def on_started(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]

        try:
            test_socket = socket.socket()
            test_socket.bind((local_host, local_port))
            test_socket.close()
        except OSError as exc:
            raise ListenerStartError(
                f"An error occurred while attempting to start the listener. Listener "
                f"was unable to bind to the provided host and port due to the "
                f"following socket error: {exc}",
            ) from None

    async def on_running(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]

        async def handle_agent(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
        ) -> None:
            agent_handler = _AgentHandler(
                logger=self.logger,
                connected_agents_service=self.connected_agents_service,
                reader=reader,
                writer=writer,
                stop_event=self.stop_event,
            )
            await agent_handler.run_agent_handler()

        await asyncio.start_server(
            client_connected_cb=handle_agent,
            host=local_host,
            port=local_port,
        )

        await self.stop_event.wait()

    async def on_errored(self, exception: Exception) -> None:
        self.logger.error(exception)
