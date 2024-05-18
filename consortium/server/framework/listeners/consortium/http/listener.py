import json
import socket

from aiohttp import web

from consortium.server.framework.base_listener import BaseListener
from consortium.server.framework.exceptions.listener_framework_exceptions import (
    ListenerStartError,
)
from consortium.server.models.agent_models import AgentResultModel


class Listener(BaseListener):
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
            agent = self.register_agent(endpoint=request.remote)
            return web.json_response({"agent_id": str(agent.agent_id)}, status=200)

        async def handle_agent_get_tasks(request):
            try:
                agent_id = request.headers["Cookie"]
                agent = self.agents[agent_id]
            except KeyError:
                return web.Response(status=401)

            agent.register_checked_in()

            queued_tasks = []
            while True:
                task = agent.get_next_queued_task()
                if task is None:
                    break
                queued_tasks.append(task)
            tasks = [
                {
                    "task_id": str(task.task_id),
                    "command": task.command,
                    "arguments": task.arguments,
                }
                for task in queued_tasks
            ]
            return web.json_response({"tasks": tasks}, status=200)

        async def handle_agent_post_results(request):
            # JSON request body from the agent takes the form
            # {"agent_id": agent_id, "task_id": task_id "result": result}.
            try:
                json_request_body = await request.json()
            except json.JSONDecodeError:
                return web.Response(status=401)

            try:
                agent_id = json_request_body["agent_id"]
                task_id = json_request_body["task_id"]
                result = json_request_body["result"]
                agent = self.agents[agent_id]
            except KeyError:
                return web.Response(status=401)

            # See if the task ID is valid.
            try:
                _ = agent.get_running_task_by_task_id(task_id)
            except ValueError:
                return web.Response(status=401)

            # Only if the task ID is valid do we deem it a valid agent that has checked
            # in.
            agent.register_checked_in()

            result = AgentResultModel(task_id=task_id, data=result)
            agent.add_result(result)
            return web.Response(status=200)

        for url_path in registration_url_paths:
            app.add_routes([web.get(url_path, handle_agent_registration)])
        for url_path in tasks_url_paths:
            app.add_routes([web.get(url_path, handle_agent_get_tasks)])
        for url_path in results_url_paths:
            app.add_routes([web.post(url_path, handle_agent_post_results)])

        self.environment.runner = web.AppRunner(app)
        await self.environment.runner.setup()
        site = web.TCPSite(self.environment.runner, local_host, local_port)
        await site.start()
        await self.stop_listener_event.wait()
        await self.environment.runner.cleanup()

    async def on_listener_stopped(self) -> None:
        pass

    async def on_listener_cancelled(self) -> None:
        # On cancellation, we need to stop the web server, but we may cancel the
        # listener task before the web server is fully set up.
        try:
            await self.environment.runner.cleanup()
        except AttributeError:
            pass

    async def on_listener_errored(self, exc: Exception) -> None:
        pass
