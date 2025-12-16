import json
import socket

import jsonschema
from aiohttp import web
from pydantic import ValidationError

from consortium.framework.agents import AgentResultMessageModel
from consortium.framework.exceptions.listeners_framework_exceptions import (
    ListenerSpecificAgentNotFoundError,
    ListenerStartError,
)
from consortium.framework.listeners import BaseListener
from consortium.server.exceptions.framework_exceptions.agents_framework_exceptions import (
    AgentTaskNotFoundError,
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
        tasks_url_paths = self.parameters["tasks_url_paths"]
        results_url_paths = self.parameters["results_url_paths"]
        registration_url_paths = self.parameters["registration_url_paths"]

        app = web.Application(
            # Max size of 50MB for the request body. File chunks when running
            # download/upload tasking are limited to 25MB unencoded. Base64 encoding
            # adds roughly 33% overhead. When we additionally account for the headers,
            # we can expect the total size of the request to be less than 50MB.
            client_max_size=52428800,
        )

        async def handle_agent_registration(request):
            agent_registration_schema = {
                "type": "object",
                "properties": {
                    "is_admin": {"type": "boolean"},
                    "os": {"type": "string"},
                    "version": {"type": "string"},
                    "arch": {"type": "string"},
                    "pid": {"type": "integer"},
                    "locale": {"type": "string"},
                    "local_host_address": {"type": "string"},
                    "hostname": {"type": "string"},
                },
            }

            try:
                json_request_body = await request.json()
                jsonschema.validate(json_request_body, agent_registration_schema)
            except (json.JSONDecodeError, jsonschema.ValidationError):
                return web.Response(status=401)

            # TODO: Only one agent type is supported for this listener type.
            agent = await self.agents_manager.register_new_connected_agent(
                agent_type="consortium/agents/http",
                endpoint=request.remote,
                remote_host_address=request.remote,
                **json_request_body,
            )
            self._logger.info(
                "Agent '{}' checked in from endpoint: {}",
                str(agent),
                request.remote,
            )
            return web.json_response({"agent_id": str(agent.agent_id)}, status=200)

        async def handle_agent_getting_tasks(request):
            try:
                agent_id = request.headers["Cookie"]
                agent = self.agents_manager.get_connected_agent_by_agent_id(
                    agent_id=agent_id,
                )
            except ListenerSpecificAgentNotFoundError:
                return web.Response(status=401)
            except KeyError:  # No Cookie header provided
                return web.Response(status=401)

            await self.agents_manager.check_in_connected_agent_by_agent_id(
                agent_id=agent_id,
            )

            agent_messages = []
            while True:
                agent_message = agent.get_next_task_message_without_waiting()

                if agent_message is None:
                    break

                agent_messages.append(agent_message.to_json())
            return web.json_response(agent_messages, status=200)

        async def handle_agent_posting_results(request):
            # Validate JSON structure result from agent.
            agent_result_schema = {
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

            json_request_body = await request.json()
            try:
                jsonschema.validate(json_request_body, agent_result_schema)
            except (json.JSONDecodeError, jsonschema.ValidationError):
                self.logger.warning(
                    "Received invalid agent result JSON data from agent: {}. Responded "
                    "with 401 Unauthorized",
                    json_request_body,
                )
                return web.Response(status=401)

            agent_id = json_request_body["agent_id"]
            task_id = json_request_body["task_id"]
            success = json_request_body["result"]["success"]
            message = json_request_body["result"]["message"]
            data = json_request_body["result"]["data"]

            # Check if the agent ID is valid.
            try:
                agent = self.agents_manager.get_connected_agent_by_agent_id(
                    agent_id=agent_id,
                )
            except ListenerSpecificAgentNotFoundError:
                self.logger.warning(
                    "Agent checked in with an invalid agent ID: {}. Responded with 401 "
                    "Unauthorized",
                    agent_id,
                )
                return web.Response(status=401)

            # Check if the task ID is valid.
            try:
                _ = agent.get_running_task_by_task_id(task_id)
            except AgentTaskNotFoundError:
                self.logger.warning(
                    "Agent {} checked in and posted a result with an invalid task ID: "
                    "{}. Responded with 401 Unauthorized.",
                    str(agent),
                    task_id,
                )
                return web.Response(status=401)

            # Only if the task ID is valid do we consider it a valid agent that has
            # checked in.
            await self.agents_manager.check_in_connected_agent_by_agent_id(
                agent_id=agent_id,
            )

            # Validate the values.
            try:
                result_message = AgentResultMessageModel(
                    task_id=task_id,
                    success=success,
                    message=message,
                    data=data,
                )
            except ValidationError:
                return web.Response(status=401)

            await agent.add_result_message(result_message=result_message)
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

    async def on_errored(self, exception: Exception) -> None:
        self.logger.error(exception)
