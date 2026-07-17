import json
import socket

import jsonschema
from aiohttp import web

from consortium.framework.listeners import BaseListener
from consortium.framework.signal_exceptions import ListenerStartError
from consortium.server.exceptions.object_exceptions.agent_object_exceptions import (
    AgentTaskNotFoundError,
    AgentTypeResolutionError,
)
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
)


class Listener(BaseListener):
    async def on_started(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]

        try:
            test_socket = socket.socket()
            test_socket.bind((local_host, local_port))
            test_socket.close()
        except Exception as exc:
            raise ListenerStartError(
                f"Listener was unable to bind to {local_host}:{local_port} due to the "
                f"following error: {exc}",
            ) from None

    async def on_running(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]
        tasks_url_paths = self.parameters["tasks_url_paths"]
        results_url_paths = self.parameters["results_url_paths"]
        registration_url_paths = self.parameters["registration_url_paths"]

        app = web.Application()

        async def handle_agent_registration(request):
            # Validate the agent registration message schema
            agent_registration_json_schema = {
                "type": "object",
                "properties": {
                    "payload_id": {"type": "string"},
                    "agent_type": {"type": "string"},
                    "user": {"type": "string"},
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

            try:
                json_request_body = await request.json()
                jsonschema.validate(json_request_body, agent_registration_json_schema)
            except json.JSONDecodeError, jsonschema.ValidationError:
                return web.Response(status=401)

            # Register the agent and create an agent record
            payload_id = json_request_body.pop("payload_id", None)
            agent_type = json_request_body.pop("agent_type", None)
            try:
                agent = self.connected_agents_service.register_agent(
                    payload_id=payload_id,
                    agent_type=agent_type,
                    endpoint=request.remote,
                    remote_host_address=request.remote,
                    **json_request_body,
                )
            except AgentTypeResolutionError:
                if agent_type:
                    self.logger.warning(
                        "Agent from {} attempted to register with an invalid agent "
                        "type: {}. Responded with 401 Unauthorized.",
                        request.remote,
                        agent_type,
                    )
                else:
                    self.logger.warning(
                        "Agent from {} attempted to register with an invalid payload "
                        "ID: {}. Responded with 401 Unauthorized.",
                        request.remote,
                        payload_id,
                    )
                return web.Response(status=401)
            self.logger.info(
                "Agent {} checked in from: {}",
                str(agent),
                request.remote,
            )
            return web.json_response({"agent_id": str(agent.agent_id)}, status=200)

        async def handle_agent_getting_tasks(request):
            # Validate the agent task message schema
            try:
                agent_id = request.headers["Cookie"]
            except KeyError:
                self.logger.warning(
                    "Unidentified client {} attempted to retrieve tasks without "
                    "providing an agent ID in the Cookie header. Responded with 401 "
                    "Unauthorized.",
                    request.remote,
                )
                return web.Response(status=401)

            # Retrieve all pending task messages for the agent (non-blocking)
            try:
                task_messages = await self.connected_agents_service.get_next_agent_task_messages_by_agent_id(
                    agent_id=agent_id,
                    count=None,  # Get all available task messages
                    block=False,  # Don't block, return immediately
                )
            except AgentNotFoundError:
                self.logger.warning(
                    "Agent from {} attempted to retrieve tasks with an invalid agent "
                    "ID '{}'. Responded with 401 Unauthorized.",
                    request.remote,
                    agent_id,
                )
                return web.Response(status=401)

            for message in task_messages:
                if message.payload is None:
                    # Serialize task messages to JSON for the wire protocol, if binary payloads
                    # were provided attach them as multipart data
                    task_messages_json = [msg.to_json() for msg in task_messages]
                    return web.json_response(task_messages_json, status=200)

        async def handle_agent_posting_results(request):
            # Validate the agent result message schema
            agent_result_json_schema = {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
                "required": ["task_id", "success", "message", "data"],
                "additionalProperties": False,
            }

            try:
                agent_id = request.headers["Cookie"]
            except KeyError:
                self.logger.warning(
                    "Unidentified client {} attempted to send results without "
                    "providing an agent ID in the Cookie header. Responded with 401 "
                    "Unauthorized.",
                    request.remote,
                )
                return web.Response(status=401)

            # Handle results that do not include multipart payloads and only have JSON
            if request.content_type == "application/json":
                try:
                    result_json = await request.json()
                    jsonschema.validate(result_json, agent_result_json_schema)
                except json.JSONDecodeError, jsonschema.ValidationError:
                    self.logger.warning(
                        "Unidentified client {} sent malformed agent result data. "
                        "JSON data was not valid result JSON. Responded with 401 "
                        "Unauthorized.",
                        request.remote,
                    )
                    return web.Response(status=401)

                task_id = result_json["task_id"]
                success = result_json["success"]
                message = result_json["message"]
                data = result_json["data"]
                payload = None
            # Handle results that include multipart payloads
            elif request.content_type == "multipart/form-data":
                reader = await request.multipart()
                result_json = None
                payload = None

                # Extract parts from the multipart data, expecting "json" and "payload"
                async for part in reader:
                    if part.name == "json":
                        try:
                            json_bytes = await part.read()
                            result_json = json.loads(json_bytes.decode("utf-8"))
                            jsonschema.validate(result_json, agent_result_json_schema)
                        except (
                            json.JSONDecodeError,
                            jsonschema.ValidationError,
                        ):
                            self.logger.warning(
                                "Unidentified client {} sent malformed agent result "
                                "data. JSON data was not valid result JSON. Responded "
                                "with 401 Unauthorized.",
                                request.remote,
                            )
                            return web.Response(status=401)
                    elif part.name == "payload":
                        payload = await part.read()

                if result_json is None or payload is None:
                    self.logger.warning(
                        "Unidentified client {} sent malformed agent result data. "
                        "Multipart result response did not contain both 'json' and "
                        "'payload'. Responded with 401 Unauthorized.",
                        request.remote,
                    )
                    return web.Response(status=401)

                task_id = result_json["task_id"]
                success = result_json["success"]
                message = result_json["message"]
                data = result_json["data"]
            else:
                self.logger.warning(
                    "Unidentified client {} sent agent result data with unsupported "
                    "Content-Type: {}. Responded with 401 Unauthorized.",
                    request.remote,
                    request.content_type,
                )
                return web.Response(status=401)

            # Submit the agent result after validation
            try:
                await self.connected_agents_service.submit_result_by_agent_id(
                    agent_id=agent_id,
                    task_id=task_id,
                    success=success,
                    message=message,
                    data=data,
                    payload=payload,
                )
            except AgentNotFoundError:
                self.logger.warning(
                    "Agent from {} checked in with an invalid agent ID: {}. Responded "
                    "with 401 Unauthorized.",
                    request.remote,
                    agent_id,
                )
                return web.Response(status=401)
            except AgentTaskNotFoundError:
                self.logger.warning(
                    "Agent from {} posted a result with an invalid task ID: {}. "
                    "Responded with 401 Unauthorized.",
                    request.remote,
                    task_id,
                )
                return web.Response(status=401)

            return web.Response(status=200)

        for url_path in registration_url_paths:
            app.add_routes([web.post(url_path, handle_agent_registration)])
        for url_path in tasks_url_paths:
            app.add_routes([web.get(url_path, handle_agent_getting_tasks)])
        for url_path in results_url_paths:
            app.add_routes([web.post(url_path, handle_agent_posting_results)])

        self.environment.runner = web.AppRunner(app)
        await self.environment.runner.setup()
        site = web.TCPSite(self.environment.runner, local_host, local_port)
        await site.start()
        await self.stop_event.wait()

    async def on_stopped(self) -> None:
        await self.environment.runner.cleanup()

    async def on_cancelled(self) -> None:
        # On cancellation, we need to stop the web server, but we may cancel the
        # listener task before the web server is fully set up.
        try:
            await self.environment.runner.cleanup()
        except AttributeError:
            pass
