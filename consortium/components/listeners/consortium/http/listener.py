import json

from aiohttp import MultipartWriter, web

from consortium.framework.agents import Payload, PayloadTooLargeError
from consortium.framework.agents.agent_message_models import (
    RegistrationMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.listeners import BaseListener
from consortium.framework.signal_exceptions import ListenerStartError
from consortium.server.exceptions.object_exceptions.agent_object_exceptions import (
    AgentTaskNotFoundError,
    AgentTypeResolutionError,
)
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
)

_MAX_PAYLOAD_SIZE = 100 * 1024 * 1024


class Listener(BaseListener):
    # Every rejection from every route answers a bare 401, whether the cause is a bad
    # agent ID, malformed JSON, a schema violation or an oversized body. This is
    # deliberate: differential status codes let a scanner probing the URL paths tell a
    # real ingress endpoint from an unrelated 404, so do not "correct" these into
    # 400/413/422.
    async def on_started(self) -> None:
        self.event_logger.info("Starting listener...")

        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]
        tasks_url_paths = self.parameters["tasks_url_paths"]
        results_url_paths = self.parameters["results_url_paths"]
        registration_url_paths = self.parameters["registration_url_paths"]

        # Bound request POST sizes to 16 MiB (much greater than the upload/download
        # chunk defaults of 8Mib). This bounds both JSON and payload binary data
        app = web.Application(client_max_size=16 * 1024 * 1024)

        def reject(request, reason, *args):
            self.logger.warning(
                "Rejected client {}: " + reason + " Responded with 401 Unauthorized.",
                request.remote,
                *args,
            )
            return web.Response(status=401)

        async def handle_agent_registration(request):
            # `RegistrationMessageModel` is the shared wire contract for registration,
            # so validation is just parsing into it. `ValueError` covers both the JSON
            # decode failure and pydantic's `ValidationError`, which subclasses it,
            # while an oversized body arrives as `HTTPRequestEntityTooLarge` from
            # `client_max_size`.
            try:
                registration = RegistrationMessageModel.model_validate(
                    await request.json()
                )
            except ValueError, web.HTTPRequestEntityTooLarge:
                return reject(request, "sent a malformed or oversized registration.")

            # An agent behind a relay or proxy is the only party that knows its own
            # address, so its own report wins. Fill in what we observed only where it
            # reported nothing.
            observed = {}
            if not registration.endpoint:
                observed["endpoint"] = request.remote
            if registration.remote_ip is None:
                observed["remote_ip"] = request.remote
            if observed:
                registration = registration.model_copy(update=observed)

            # Register the agent and create an agent record
            try:
                agent = self.connected_agents_service.register_agent(
                    registration_message=registration,
                )
            except AgentTypeResolutionError:
                if registration.agent_type:
                    return reject(
                        request,
                        "registered with an invalid agent type: {}.",
                        registration.agent_type,
                    )
                return reject(
                    request,
                    "registered with an invalid payload ID: {}.",
                    registration.payload_id,
                )
            self.logger.info(
                "Agent {} checked in from: {}",
                str(agent),
                request.remote,
            )
            return web.json_response({"agent_id": str(agent.agent_id)}, status=200)

        async def handle_agent_getting_task_message(request):
            # Agents identify themselves with their agent ID in the Cookie header
            try:
                agent_id = request.headers["Cookie"]
            except KeyError:
                return reject(request, "retrieved tasks without an agent ID.")

            # Retrieval performs the agent check-in for us.
            try:
                task_message = await self.connected_agents_service.get_next_task_message_sequential(
                    agent_id=agent_id,
                    timeout=0,  # Don't block, return immediately
                )
            except AgentNotFoundError:
                return reject(
                    request,
                    "retrieved tasks with an invalid agent ID: {}.",
                    agent_id,
                )

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
                    binary_data = await task_message.payload.read()
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
            try:
                agent_id = request.headers["Cookie"]
            except KeyError:
                return reject(request, "posted a result without an agent ID.")

            # Decoding the body and validating it against the shared wire contract are one
            # step: `from_json` keeps the binary payload out of band so an agent cannot
            # inject one through the JSON. A single `ValueError` covers the JSON decode
            # failure, a bad UTF-8 part, and pydantic's `ValidationError`, all of which
            # subclass it.
            try:
                # Handle results that do not include multipart payloads and only have JSON
                if request.content_type == "application/json":
                    task_output_message_json = await request.json()
                    payload = None
                # Handle results that include multipart payloads
                elif request.content_type == "multipart/form-data":
                    reader = await request.multipart()
                    task_output_message_json = None
                    payload = None

                    # Extract parts from the multipart data, expecting "json" and
                    # "payload"
                    async for part in reader:
                        if part.name == "json":
                            json_bytes = await part.read()
                            task_output_message_json = json.loads(
                                json_bytes.decode("utf-8")
                            )
                        elif part.name == "payload":
                            try:
                                payload = await Payload.from_async_iterable(
                                    part,
                                    max_size=_MAX_PAYLOAD_SIZE,
                                    filename=part.filename,
                                    content_type=part.headers.get("Content-Type"),
                                )
                            except PayloadTooLargeError:
                                return reject(
                                    request,
                                    "posted a payload over the {} byte maximum.",
                                    _MAX_PAYLOAD_SIZE,
                                )

                    if task_output_message_json is None or payload is None:
                        return reject(
                            request,
                            "posted a multipart result missing its 'json' or 'payload' "
                            "part.",
                        )
                else:
                    return reject(
                        request,
                        "posted a result with an unsupported Content-Type: {}.",
                        request.content_type,
                    )

                output = TaskOutputMessageModel.from_json(
                    task_output_message_json,
                    payload=payload,
                )
            except ValueError, web.HTTPRequestEntityTooLarge:
                return reject(request, "posted a malformed or oversized result.")

            # Submit the agent result after validation
            try:
                await self.connected_agents_service.dispatch_task_output_message(
                    agent_id=agent_id,
                    task_output_message=output,
                )
            except AgentNotFoundError:
                return reject(
                    request,
                    "posted a result with an invalid agent ID: {}.",
                    agent_id,
                )
            except AgentTaskNotFoundError:
                return reject(
                    request,
                    "posted a result with an invalid task ID: {}.",
                    output.task_id,
                )

            return web.Response(status=200)

        for url_path in registration_url_paths:
            app.add_routes([web.post(url_path, handle_agent_registration)])
        for url_path in tasks_url_paths:
            app.add_routes([web.get(url_path, handle_agent_getting_task_message)])
        for url_path in results_url_paths:
            app.add_routes([web.post(url_path, handle_agent_posting_task_message)])

        try:
            self.environment.runner = web.AppRunner(app)
            await self.environment.runner.setup()
            site = web.TCPSite(self.environment.runner, local_host, local_port)
            await site.start()
            self.event_logger.success(f"Listener started on {local_host}:{local_port}")
        except OSError as exc:
            self.event_logger.error(
                f"Listener was unable to bind to {local_host}:{local_port} due to the "
                f"following error: {exc}.",
            )
            raise ListenerStartError(
                f"Listener was unable to bind to {local_host}:{local_port} due to the "
                f"following error: {exc}.",
            ) from None

    async def on_running(self) -> None:
        await self.stop_event.wait()

    async def on_stopped(self) -> None:
        await self.environment.runner.cleanup()

    async def on_cancelled(self) -> None:
        # On cancellation, we need to stop the web server, but we may cancel the
        # listener task before the web server is fully set up so check for the runner
        if hasattr(self.environment, "runner"):
            await self.environment.runner.cleanup()
