# Complete Listener Profile

Here are the three files of the TCP JSON Listener combining every concept covered in
[Project Setup](project-setup.md) through [Listener Conventions](listener-conventions.md).
This is the full source for a minimal but complete listener profile.

## listener_type.py

```python
from consortium.framework.listeners import BaseListenerType


class ListenerType(BaseListenerType):
    name = "tcp_json"
```

## listener_template.py

```python
from consortium.framework.exceptions import OptionValueValidationError
from consortium.framework.listeners import BaseListenerTemplate
from consortium.framework.options import SingleValueOption

from .listener import Listener
from .listener_type import ListenerType


def _validate_loopback_warning(parameters: dict) -> None:
    if parameters["local_host"] != "127.0.0.1" and parameters["local_port"] < 1024:
        raise OptionValueValidationError(
            "Ports below 1024 require root on non-loopback interfaces. "
            "Use a port >= 1024 or bind to 127.0.0.1.",
        )


class ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.tcp_json"
    name = "TCP JSON Listener"
    description = (
        "A raw TCP listener that exchanges newline-delimited JSON messages "
        "with connected agents."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Your Name"}

    listener      = Listener
    listener_type = ListenerType
    validating_function = _validate_loopback_warning
    options = {
        SingleValueOption(
            name="local_host",
            description="IP address to bind the TCP server to.",
            required=True,
            default_value="0.0.0.0",
            value_type=str,
        ),
        SingleValueOption(
            name="local_port",
            description="TCP port to listen on.",
            required=True,
            default_value=4444,
            value_type=int,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=65535,
        ),
        SingleValueOption(
            name="name",
            description="Display name for this listener instance.",
            required=True,
            default_value="",
            value_type=str,
        ),
    }

    def resolve_listener_name(self, parameters: dict) -> str:
        return parameters["name"]

    def resolve_listener_endpoint(self, parameters: dict) -> str:
        return f"tcp://{parameters['local_host']}:{parameters['local_port']}"
```

## listener.py

```python
import asyncio
import json
import socket

from consortium.framework.exceptions import ListenerStartError
from consortium.framework.listeners import BaseListener
from consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions import (
    AgentNotFoundError,
    AgentTypeResolutionError,
)


class Listener(BaseListener):

    async def on_started(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            probe.bind((local_host, local_port))
            probe.close()
        except OSError as exc:
            raise ListenerStartError(
                f"Cannot bind to {local_host}:{local_port}: {exc}",
            ) from None
        self.logger.info("Ready on {}:{}.", local_host, local_port)

    async def on_running(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]

        async def handle_client(reader, writer):
            remote = writer.get_extra_info("peername", ("?", "?"))
            remote_addr = f"{remote[0]}:{remote[1]}"
            try:
                await self._handle_session(reader, writer, remote_addr)
            except Exception as exc:
                self.logger.warning("Session from {} aborted: {}", remote_addr, exc)
            finally:
                writer.close()

        server = await asyncio.start_server(handle_client, local_host, local_port)
        self.environment.server = server
        self.logger.info("Listening on {}:{}.", local_host, local_port)
        async with server:
            await self.stop_event.wait()

    async def on_stopped(self) -> None:
        if hasattr(self.environment, "server"):
            self.environment.server.close()
            await self.environment.server.wait_closed()
        self.logger.info("Stopped.")

    async def on_cancelled(self) -> None:
        if hasattr(self.environment, "server"):
            self.environment.server.close()

    async def _handle_session(self, reader, writer, remote_addr):
        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                writer.write(b'{"error": "invalid json"}\n')
                await writer.drain()
                continue

            msg_type = message.get("type")
            if msg_type == "register":
                await self._handle_registration(message, writer, remote_addr)
            elif msg_type == "check_in":
                await self._handle_check_in(message, writer)
            elif msg_type == "result":
                await self._handle_result(message, writer)
            else:
                writer.write(b'{"error": "unknown message type"}\n')
                await writer.drain()

    async def _handle_registration(self, message, writer, remote_addr):
        try:
            agent = self.connected_agents_service.register_agent(
                payload_id=message.get("payload_id"),
                agent_type=message.get("agent_type"),
                endpoint=remote_addr,
                remote_host_address=remote_addr,
                user=message.get("user"),
                is_admin=message.get("is_admin"),
                os=message.get("os"),
                hostname=message.get("hostname"),
            )
        except AgentTypeResolutionError:
            writer.write(b'{"error": "unauthorized"}\n')
            await writer.drain()
            return
        writer.write((json.dumps({"agent_id": str(agent.agent_id)}) + "\n").encode())
        await writer.drain()

    async def _handle_check_in(self, message, writer):
        try:
            tasks = await self.connected_agents_service.get_next_agent_task_messages_by_agent_id(
                agent_id=message.get("agent_id", ""),
                count=None,
                block=False,
            )
        except AgentNotFoundError:
            writer.write(b'{"error": "unauthorized"}\n')
            await writer.drain()
            return
        writer.write((json.dumps([t.to_json() for t in tasks]) + "\n").encode())
        await writer.drain()

    async def _handle_result(self, message, writer):
        try:
            await self.connected_agents_service.submit_result_by_agent_id(
                agent_id=message.get("agent_id", ""),
                task_id=message["task_id"],
                success=message["success"],
                message=message.get("message", ""),
                data=message.get("data", {}),
            )
        except (AgentNotFoundError, KeyError):
            writer.write(b'{"error": "unauthorized"}\n')
            await writer.drain()
            return
        writer.write(b'{"ok": true}\n')
        await writer.drain()
```

## Further examples

`consortium/components/listeners/consortium/http/` is the most complete reference
implementation. Beyond the basic pattern above, it demonstrates:

- Using `aiohttp` in `on_running` instead of raw asyncio streams
- Validating agent message schemas before processing
- Handling binary payloads via multipart form data in result submissions
- Multiple configurable URL paths for tasks, results, and registration routes
- The `validating_function` pattern for enforcing that all URL paths are unique
