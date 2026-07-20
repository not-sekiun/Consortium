import json
import socket

import jsonschema
from aiohttp import MultipartWriter, web

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
                    "local_ip": {"type": "string"},
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
                    remote_ip=request.remote,
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

        async def handle_agent_getting_task_message(request):
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

            try:
                task_message = await self.connected_agents_service.get_next_task_message_sequential(
                    agent_id=agent_id,
                    timeout=0,  # Don't block, return immediately
                )
            except AgentNotFoundError:
                self.logger.warning(
                    "Agent from {} attempted to retrieve tasks with an invalid agent "
                    "ID '{}'. Responded with 401 Unauthorized.",
                    request.remote,
                    agent_id,
                )
                return web.Response(status=401)

            if task_message is None:  # No task messages to report
                return web.Response(status=204)
            elif task_message.payload is None:
                # Serialize task messages to JSON for the wire protocol, if binary payloads
                # were provided attach them as multipart data
                return web.json_response(task_message.to_json(), status=200)
            else:
                # Handle task messages with binary payloads using a multipart response
                with MultipartWriter() as writer:
                    # JSON part
                    json_part = writer.append_json(task_message.to_json())
                    json_part.set_content_disposition("form-data", name="json")

                    # Payload part
                    binary_data = task_message.payload
                    bin_part = writer.append(binary_data)
                    bin_part.set_content_disposition("form-data", name="payload")
                    bin_part.headers["Content-Type"] = "application/octet-stream"

                return web.Response(
                    body=writer,
                    headers={
                        "Content-Type": f"multipart/mixed; boundary={writer.boundary}"
                    },
                )

        async def handle_agent_posting_task_message(request):
            # Validate the agent result message schema
            task_output_message_json_schema = {
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
                    "Unidentified client {} attempted to post data to endpoint without "
                    "providing an agent ID in the Cookie header. Responded with 401 "
                    "Unauthorized.",
                    request.remote,
                )
                return web.Response(status=401)

            # Handle results that do not include multipart payloads and only have JSON
            if request.content_type == "application/json":
                try:
                    task_output_message_json = await request.json()
                    jsonschema.validate(
                        task_output_message_json, task_output_message_json_schema
                    )
                except json.JSONDecodeError, jsonschema.ValidationError:
                    self.logger.warning(
                        "Unidentified client {} posted malformed JSON data. Responded "
                        "with 401 Unauthorized.",
                        request.remote,
                    )
                    return web.Response(status=401)

                task_id = task_output_message_json["task_id"]
                success = task_output_message_json["success"]
                message = task_output_message_json["message"]
                data = task_output_message_json["data"]
                payload = None
            # Handle results that include multipart payloads
            elif request.content_type == "multipart/form-data":
                reader = await request.multipart()
                task_output_message_json = None
                payload = None

                # Extract parts from the multipart data, expecting "json" and "payload"
                async for part in reader:
                    if part.name == "json":
                        try:
                            json_bytes = await part.read()
                            task_output_message_json = json.loads(
                                json_bytes.decode("utf-8")
                            )
                            jsonschema.validate(
                                task_output_message_json,
                                task_output_message_json_schema,
                            )
                        except (
                            json.JSONDecodeError,
                            jsonschema.ValidationError,
                        ):
                            self.logger.warning(
                                "Unidentified client {} posted malformed JSON data. "
                                "Responded with 401 Unauthorized.",
                                request.remote,
                            )
                            return web.Response(status=401)
                    elif part.name == "payload":
                        payload = await part.read()

                if task_output_message_json is None or payload is None:
                    self.logger.warning(
                        "Unidentified client {} posted malformed multipart request. "
                        "Multipart request did not contain both a 'json' and "
                        "'payload' field. Responded with 401 Unauthorized.",
                        request.remote,
                    )
                    return web.Response(status=401)

                task_id = task_output_message_json["task_id"]
                success = task_output_message_json["success"]
                message = task_output_message_json["message"]
                data = task_output_message_json["data"]
            else:
                self.logger.warning(
                    "Unidentified client {} posted malformed multipart request with "
                    "unsupported Content-Type '{}'. Responded with 401 Unauthorized.",
                    request.remote,
                    request.content_type,
                )
                return web.Response(status=401)

            # Submit the agent result after validation
            try:
                await self.connected_agents_service.dispatch_task_output_message(
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
            app.add_routes([web.get(url_path, handle_agent_getting_task_message)])
        for url_path in results_url_paths:
            app.add_routes([web.post(url_path, handle_agent_posting_task_message)])

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
