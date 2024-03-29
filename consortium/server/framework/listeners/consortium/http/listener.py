import asyncio
import socket

from aiohttp import web

from consortium.server.framework.base_listener import BaseListener
from consortium.server.framework.framework_exceptions import ListenerStartError


class Listener(BaseListener):
    async def on_listener_started(self) -> None:
        local_host = self.options["local_host"].get_option_value()
        local_port = self.options["local_port"].get_option_value()

        try:
            test_socket = socket.socket()
            test_socket.bind((local_host, local_port))
            test_socket.close()
        except socket.error as exc:
            raise ListenerStartError(
                f"Unable to bind to the provided host and port: {exc}",
            )

    async def on_listener_running(self) -> None:
        local_host = self.options["local_host"].get_option_value()
        local_port = self.options["local_port"].get_option_value()
        tasks_url_paths = self.options["tasks_url_paths"].get_option_value()
        results_url_paths = self.options["results_url_paths"].get_option_value()
        registration_url_paths = self.options[
            "registration_url_paths"
        ].get_option_value()

        app = web.Application()
        self.state.shutdown_signal = asyncio.Event()

        async def handle_registration(_):
            agent = self.create_agent()
            return web.json_response({"agent_id": str(agent.agent_id)}, status=200)

        async def handle_tasks(_):
            return web.json_response({"tasks": []}, status=200)

        async def handle_results(_):
            return web.Response(status=200)

        for url_path in registration_url_paths:
            app.add_routes([web.get(url_path, handle_registration)])
        for url_path in tasks_url_paths:
            app.add_routes([web.get(url_path, handle_tasks)])
        for url_path in results_url_paths:
            app.add_routes([web.post(url_path, handle_results)])

        self.state.runner = web.AppRunner(app)
        await self.state.runner.setup()
        site = web.TCPSite(self.state.runner, local_host, local_port)
        await site.start()
        await self.state.shutdown_signal.wait()
        await self.state.runner.cleanup()

    async def on_listener_stopped(self) -> None:
        self.state.shutdown_signal.set()

    async def on_listener_cancelled(self) -> None:
        # On cancellation, we need to stop the web server, but we may cancel the
        # listener task before the web server is fully set up.
        try:
            self.state.shutdown_signal.set()
            try:
                await self.state.runner.cleanup()
            except AttributeError:
                pass
        except AttributeError:
            pass

    async def on_listener_errored(self, exc: Exception) -> None:
        pass
