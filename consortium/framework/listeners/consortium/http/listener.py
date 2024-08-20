import json
import socket

import jsonschema
from aiohttp import web

from consortium.framework.agents.consortium.http.agent_type import AGENT_TYPE
from consortium.framework.base_listener import BaseListener
from consortium.framework.exceptions.listeners_framework_exceptions import (
    ListenerSpecificAgentNotFoundError,
    ListenerStartError,
)
from consortium.framework.listeners.consortium.http.listener_type import LISTENER_TYPE
from consortium.server.models.agent_models import AgentResultModel, AgentResultState


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
        tasks_url_paths = self.parameters["tasks_url_paths"]
        results_url_paths = self.parameters["results_url_paths"]
        registration_url_paths = self.parameters["registration_url_paths"]

        app = web.Application()

        async def handle_agent_registration(request):
            # Only one agent type is supported for this listener type.
            agent = self.agents_manager.register_new_agent(
                agent_type=AGENT_TYPE,
                endpoint=request.remote,
                remote_host_address=request.remote,
            )
            return web.json_response({"agent_id": str(agent.agent_id)}, status=200)

        async def handle_agent_getting_tasks(request):
            try:
                agent_id = request.headers["Cookie"]
                agent = self.agents_manager.get_agent_by_agent_id(agent_id)
            except ListenerSpecificAgentNotFoundError:
                return web.Response(status=401)

            self.agents_manager.check_in_registered_agent_by_agent_id(agent=agent)

            tasks = []
            for task in agent.get_next_agent_message_without_waiting():
                if task is None:
                    break

                task_json_data = json.dumps(
                    {
                        "task_id": task.task_id,
                        "command": task.command,
                        "arguments": task.arguments,
                        "data": task.data,
                    },
                )
                tasks.append(task_json_data)
            return web.json_response({"tasks": tasks}, status=200)

        async def handle_agent_posting_results(request):
            # JSON request body from the agent takes the form
            # {"agent_id": agent_id, "task_id": task_id "result": result}.
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
            try:
                json_request_body = await request.json()
                jsonschema.validate(json_request_body, agent_result_schema)
            except json.JSONDecodeError:
                return web.Response(status=401)
            except jsonschema.ValidationError:
                return web.Response(status=401)

            agent_id = json_request_body["agent_id"]
            task_id = json_request_body["task_id"]
            result = json_request_body["result"]

            # Check if the agent ID is valid.
            try:
                agent = self.agents_manager.get_registered_agent_by_agent_id(agent_id)
            except ListenerSpecificAgentNotFoundError:
                return web.Response(status=401)

            # Check if the task ID is valid.
            try:
                _ = agent.get_running_task_by_task_id(task_id)
            except ValueError:
                return web.Response(status=401)

            # Only if the task ID is valid do we consider it a valid agent that has
            # checked in.
            agent.register_checked_in()

            if result["success"]:
                agent_result_state = AgentResultState.SUCCESS
            elif not result["success"]:
                agent_result_state = AgentResultState.FAILED
            else:
                assert (
                    False
                ), "The 'success' field in the agent result was not a boolean."

            result = AgentResultModel(
                task_id=task_id,
                state=agent_result_state,
                message=result["message"],
                data=result["data"],
            )
            agent.add_result(result)
            return web.Response(status=200)

        for url_path in registration_url_paths:
            app.add_routes([web.get(url_path, handle_agent_registration)])
        for url_path in tasks_url_paths:
            app.add_routes([web.get(url_path, handle_agent_getting_tasks)])
        for url_path in results_url_paths:
            app.add_routes([web.post(url_path, handle_agent_posting_results)])

        self.environment.runner = web.AppRunner(app)
        await self.environment.runner.setup()
        site = web.TCPSite(self.environment.runner, local_host, local_port)
        await site.start()
        await self.stop_listener_event.wait()

    async def on_listener_stopped(self) -> None:
        await self.environment.runner.cleanup()

    async def on_listener_cancelled(self) -> None:
        # On cancellation, we need to stop the web server, but we may cancel the
        # listener task before the web server is fully set up.
        try:
            await self.environment.runner.cleanup()
        except AttributeError:
            pass

    async def on_listener_errored(self, exception: Exception) -> None:
        self.listener_logger.error(exception)
