from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import IO, Any, Literal

import aiohttp
from aiohttp import ClientConnectionError
from loguru import logger
from pydantic import JsonValue

from consortium.client.exceptions.rest_api_exceptions import (
    InvalidRestAPICredentialsError,
    InvalidServerRestAPILoginResponseError,
    RestAPIAlreadyLoggedInError,
    RestAPIConnectionError,
    RestAPINotLoggedInError,
    RestAPIOperationError,
)
from consortium.client.models.logging_models import LoggerType


def _requires_authentication(
    async_func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def wrapper(self, *args, **kwargs) -> Any:
        if not self.logged_in:
            raise RestAPINotLoggedInError(
                remote_host=self.remote_host,
                remote_port=self.remote_port,
            )

        return await async_func(self, *args, **kwargs)

    return wrapper


# TODO: Consider transitioning to auto generation of client code using OpenAPI
#    specifications once the API stabilizes. Figure out how to not have the API be name
#    mangled.
class RestAPI:
    def __init__(
        self,
        username: str,
        password: str,
        remote_host: str,
        remote_port: int,
    ):
        self.username = username
        self.password = password
        self.remote_host = remote_host
        self.remote_port = remote_port

        self.logged_in = False
        self.json_web_token = None

        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.CLIENT_REST_API_LOGGER
        )
        self._api_base_url = f"http://{self.remote_host}:{self.remote_port}/api"
        self._aiohttp_client_session = aiohttp.ClientSession()

    def __str__(self):
        return f"Client RestAPI ({self.remote_host}:{self.remote_port})"

    def __repr__(self):
        return (
            f"RestAPI("
            f"username={repr(self.username)}, "
            f"password={repr(self.password)},"
            f"remote_host={repr(self.remote_host)}, "
            f"remote_port={repr(self.remote_port)}"
            f")"
        )

    async def connect(self) -> None:
        if self.logged_in:
            raise RestAPIAlreadyLoggedInError(
                remote_host=self.remote_host,
                remote_port=self.remote_port,
                username=self.username,
            )

        try:
            response = await self._aiohttp_client_session.post(
                f"{self._api_base_url}/login",
                data={
                    "username": self.username,
                    "password": self.password,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            )
        # Close the client session if any connection related exception is raised
        # while attempting to log in to the server.
        except ClientConnectionError as exc:
            await self._aiohttp_client_session.close()
            raise RestAPIConnectionError(
                remote_host=self.remote_host,
                remote_port=self.remote_port,
                username=self.username,
            ) from exc

        # The server returns a generic 401 response for failed logins.
        if response.status == 401:
            raise InvalidRestAPICredentialsError(
                remote_host=self.remote_host,
                remote_port=self.remote_port,
                username=self.username,
            )
        response_json = await response.json()

        # If any other status code is returned other than 200, or if the response does
        # not contain the expected fields, conclude that the server returned an invalid
        # response.
        if (
            response_json["token_type"] != "bearer"
            or "access_token" not in response_json
        ) or response.status != 200:
            raise InvalidServerRestAPILoginResponseError(
                remote_host=self.remote_host,
                remote_port=self.remote_port,
                username=self.username,
            )

        self.json_web_token = response_json["access_token"]
        self._aiohttp_client_session.headers.update(
            {"Authorization": f"Bearer {response_json['access_token']}"},
        )
        self.logged_in = True

    async def disconnect(self) -> None:
        if not self.logged_in:
            raise RestAPINotLoggedInError(
                remote_host=self.remote_host, remote_port=self.remote_port
            )

        try:
            await self.logout()
        except ClientConnectionError:
            pass
        except RestAPIOperationError as exc:
            if exc.status_code != 401:
                raise exc from None
        self._aiohttp_client_session.headers.pop("Authorization")
        await self._aiohttp_client_session.close()
        self.logged_in = False

    # Wrapper methods for the /api/login API endpoints.
    async def login(self, username: str, password: str) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/login",
            data={
                "username": username,
                "password": password,
            },
        )

    # Wrapper methods for the /api/logout API endpoint.
    @_requires_authentication
    async def logout(self) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/logout",
        )

    # Wrapper methods for the /api/server API endpoints.
    @_requires_authentication
    async def get_server_release(self) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/server/release",
        )

    @_requires_authentication
    async def get_server_config(self) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/server/config",
        )

    # Wrapper methods for the /api/listener-templates API endpoint.
    @_requires_authentication
    async def get_all_listener_templates(self) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/listener-templates/all",
        )

    @_requires_authentication
    async def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/listener-templates/{listener_template_id}",
        )

    @_requires_authentication
    async def create_listener_through_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
        listener_template_option_values: dict[str, JsonValue],
        name: str | None = None,
        description: str = "",
    ) -> dict[str, JsonValue]:
        # The created listener's `name` and `description` are display metadata and are
        # sent as fields of their own, separate from the creating listener template's
        # option values. A listener template is free to declare its own option called
        # `name` or `description`: those stay inside `options` and are never conflated
        # with the fields here. A `name` of `None` leaves the server to generate one.
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/listener-templates/{listener_template_id}",
            json={
                "options": listener_template_option_values,
                "name": name,
                "description": description,
            },
        )

    # Wrapper methods for the /api/listeners API endpoint.
    @_requires_authentication
    async def get_all_listeners(self) -> list[dict[str, JsonValue]]:
        # Collection responses omit per-resource event log entries, so this endpoint
        # takes no limit/offset. Use get_listener_by_listener_id to page a specific
        # listener's event log.
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/listeners/all",
        )

    @_requires_authentication
    async def get_listener_by_listener_id(
        self,
        listener_id: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, JsonValue]:
        params = self._build_event_log_params(limit, offset)
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/listeners/{listener_id}",
            params=params if params else None,
        )

    @_requires_authentication
    async def update_listener_by_listener_id(
        self,
        listener_id: str,
        new_listener_attributes: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="PATCH",
            url=f"{self._api_base_url}/listeners/{listener_id}",
            json=new_listener_attributes,
        )

    @_requires_authentication
    async def delete_listener_by_listener_id(
        self,
        listener_id: str,
    ):
        return await self._make_api_request(
            method="DELETE",
            url=f"{self._api_base_url}/listeners/{listener_id}",
        )

    @_requires_authentication
    async def start_listener_by_listener_id(
        self, listener_id: str
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/listeners/{listener_id}/start",
        )

    @_requires_authentication
    async def stop_listener_by_listener_id(
        self, listener_id: str
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/listeners/{listener_id}/stop",
        )

    @_requires_authentication
    async def cancel_listener_by_listener_id(
        self, listener_id: str
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/listeners/{listener_id}/cancel",
        )

    # Wrapper methods for the /api/agent-templates API endpoint.
    @_requires_authentication
    async def get_all_agent_templates(self) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/agent-templates/all",
        )

    @_requires_authentication
    async def get_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/agent-templates/{agent_template_id}",
        )

    @_requires_authentication
    async def create_agent_generator_through_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
        agent_template_option_values: dict[str, JsonValue],
        name: str | None = None,
        description: str = "",
    ) -> dict[str, JsonValue]:
        # The created agent generator's `name` and `description` are display metadata and
        # are sent as fields of their own, separate from the creating agent template's
        # option values. An agent template is free to declare its own option called
        # `name` or `description`: those stay inside `options` and are never conflated
        # with the fields here. A `name` of `None` leaves the server to generate one.
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/agent-templates/{agent_template_id}",
            json={
                "options": agent_template_option_values,
                "name": name,
                "description": description,
            },
        )

    # Wrapper methods for the /api/agent-generators API endpoint.
    @_requires_authentication
    async def get_all_agent_generators(self) -> list[dict[str, JsonValue]]:
        # Collection responses omit per-resource event log entries, so this endpoint
        # takes no limit/offset. Use get_agent_generator_by_agent_generator_id to page a
        # specific generator's event log.
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/agent-generators/all",
        )

    @_requires_authentication
    async def get_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, JsonValue]:
        params = self._build_event_log_params(limit, offset)
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}",
            params=params if params else None,
        )

    @_requires_authentication
    async def update_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
        new_agent_generator_attributes: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="PATCH",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}",
            json=new_agent_generator_attributes,
        )

    @_requires_authentication
    async def delete_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="DELETE",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}",
        )

    @_requires_authentication
    async def start_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}/start",
        )

    @_requires_authentication
    async def stop_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}/stop",
        )

    @_requires_authentication
    async def cancel_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}/cancel",
        )

    # Wrapper methods for the /api/agents and /api/tasks API endpoints.
    @_requires_authentication
    async def get_all_agents(self) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/agents/all",
        )

    @_requires_authentication
    async def get_agent_by_agent_id(self, agent_id: str) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}",
        )

    @_requires_authentication
    async def get_all_agent_tasks(self) -> list[dict[str, JsonValue]]:
        # Collection responses omit per-task event log entries, so this endpoint takes no
        # limit/offset. Use get_agent_task_by_task_id to page a specific task's events.
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/tasks/all",
        )

    @_requires_authentication
    async def get_agent_task_by_task_id(
        self,
        task_id: str,
        limit: int | None = None,
        offset: int | None = None,
    ):
        params = self._build_event_log_params(limit, offset)
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/tasks/{task_id}",
            params=params if params else None,
        )

    @_requires_authentication
    async def get_all_agent_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, JsonValue]]:
        # Collection responses omit per-task event log entries, so this endpoint takes no
        # limit/offset. Use get_agent_task_by_task_id to page a specific task's events.
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/tasks/all",
            params={"agent_id": agent_id},
        )

    @_requires_authentication
    async def get_all_queued_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/tasks/all",
            params={"agent_id": agent_id, "status": "QUEUED"},
        )

    @_requires_authentication
    async def get_all_running_agent_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/tasks/all",
            params={"agent_id": agent_id, "status": "RUNNING"},
        )

    @_requires_authentication
    async def get_all_completed_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, JsonValue]]:
        tasks = await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/tasks/all",
            params={"agent_id": agent_id},
        )
        return [
            task
            for task in tasks
            if task["status"]["state"] in {"SUCCEEDED", "FAILED", "ERRORED"}
        ]

    @_requires_authentication
    async def delete_task_by_task_id(
        self,
        task_id: str,
    ) -> None:
        return await self._make_api_request(
            method="DELETE",
            url=f"{self._api_base_url}/tasks/{task_id}",
        )

    @_requires_authentication
    async def update_agent_by_agent_id(
        self,
        agent_id: str,
        new_agent_attributes: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="PATCH",
            url=f"{self._api_base_url}/agents/{agent_id}",
            json=new_agent_attributes,
        )

    @_requires_authentication
    async def delete_agent_by_agent_id(
        self,
        agent_id: str,
    ) -> None:
        return await self._make_api_request(
            method="DELETE",
            url=f"{self._api_base_url}/agents/{agent_id}",
        )

    # Wrapper methods for the /api/users API endpoint.
    @_requires_authentication
    async def get_user_info_by_user_id(
        self,
        user_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/users/{user_id}",
        )

    @_requires_authentication
    async def get_own_user_info(self) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/users/me",
        )

    @_requires_authentication
    async def get_all_users_info(self) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/users/all",
        )

    @_requires_authentication
    async def task_agent_by_agent_id(
        self,
        agent_id: str,
        command: str,
        arguments: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/agents/{agent_id}/tasks",
            json={"command": command, "arguments": arguments},
        )

    # Wrapper methods for the /api/assets API endpoint.
    async def get_all_assets(
        self,
    ) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/assets/all",
        )

    @_requires_authentication
    async def update_asset_by_resource_id(
        self,
        resource_id: str,
        new_asset_attributes: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="PATCH",
            url=f"{self._api_base_url}/assets/{resource_id}",
            json=new_asset_attributes,
        )

    @_requires_authentication
    async def delete_asset_by_resource_id(
        self,
        resource_id: str,
    ) -> None:
        return await self._make_api_request(
            method="DELETE",
            url=f"{self._api_base_url}/assets/{resource_id}",
        )

    # Wrapper methods for the /api/assets API endpoint.
    async def get_asset_by_resource_id(
        self,
        resource_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/assets/{resource_id}",
        )

    async def download_asset_by_resource_id(
        self,
        resource_id: str,
        maximum_chunk_size: int = 1024,
    ) -> AsyncGenerator[bytes]:
        async for chunk in self._stream_download_response(
            url=f"{self._api_base_url}/assets/download/{resource_id}",
            maximum_chunk_size=maximum_chunk_size,
        ):
            yield chunk

    @_requires_authentication
    async def upload_asset(
        self,
        file_object: IO,
        is_directory: bool,
        name: str = "",
        description: str = "",
        asset_directory_archive_file_format: Literal[
            ".zip",
            ".tar",
            ".tar.gz",
            ".tar.bz2",
            ".tar.xz",
        ]
        | None = None,
    ) -> dict[str, JsonValue]:
        form_data = {
            "file": file_object,
            "is_directory": str(is_directory).lower(),
            "name": name,
            "description": description,
        }
        # The server validates `directory_archive_file_format` against a `Literal` of
        # archive extensions, so the field is omitted entirely rather than sent as an
        # empty string when no format applies (every file upload, and any directory
        # upload whose format is inferred from the filename instead). An empty string
        # is not a member of that `Literal` and fails validation with a 422 before the
        # endpoint is ever reached.
        if asset_directory_archive_file_format is not None:
            form_data["directory_archive_file_format"] = (
                asset_directory_archive_file_format
            )

        return await self._make_api_request(
            method="POST",
            url=f"{self._api_base_url}/assets/upload",
            data=form_data,
        )

    # Wrapper methods for the /api/artifacts API endpoint.
    @_requires_authentication
    async def get_all_artifacts(
        self,
    ) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/artifacts/all",
        )

    @_requires_authentication
    async def get_artifact_by_resource_id(
        self,
        resource_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/artifacts/{resource_id}",
        )

    @_requires_authentication
    async def update_artifact_by_resource_id(
        self,
        resource_id: str,
        new_artifact_attributes: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="PATCH",
            url=f"{self._api_base_url}/artifacts/{resource_id}",
            json=new_artifact_attributes,
        )

    @_requires_authentication
    async def delete_artifact_by_resource_id(
        self,
        resource_id: str,
    ) -> None:
        return await self._make_api_request(
            method="DELETE",
            url=f"{self._api_base_url}/artifacts/{resource_id}",
        )

    async def download_artifact_by_resource_id(
        self,
        resource_id: str,
        maximum_chunk_size: int = 1024,
    ) -> AsyncGenerator[bytes]:
        async for chunk in self._stream_download_response(
            url=f"{self._api_base_url}/artifacts/download/{resource_id}",
            maximum_chunk_size=maximum_chunk_size,
        ):
            yield chunk

    # Wrapper methods for the /api/payloads API endpoint.
    @_requires_authentication
    async def get_all_payloads(self) -> list[dict[str, JsonValue]]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/payloads/all",
        )

    @_requires_authentication
    async def get_payload_by_resource_id(
        self,
        resource_id: str,
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="GET",
            url=f"{self._api_base_url}/payloads/{resource_id}",
        )

    @_requires_authentication
    async def update_payload_by_resource_id(
        self,
        resource_id: str,
        new_payload_attributes: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        return await self._make_api_request(
            method="PATCH",
            url=f"{self._api_base_url}/payloads/{resource_id}",
            json=new_payload_attributes,
        )

    @_requires_authentication
    async def delete_payload_by_resource_id(
        self,
        resource_id: str,
    ) -> None:
        return await self._make_api_request(
            method="DELETE",
            url=f"{self._api_base_url}/payloads/{resource_id}",
        )

    async def download_payload_by_resource_id(
        self,
        resource_id: str,
        maximum_chunk_size: int = 1024,
    ) -> AsyncGenerator[bytes]:
        async for chunk in self._stream_download_response(
            url=f"{self._api_base_url}/payloads/download/{resource_id}",
            maximum_chunk_size=maximum_chunk_size,
        ):
            yield chunk

    async def _stream_download_response(
        self,
        url: str,
        maximum_chunk_size: int,
    ) -> AsyncGenerator[bytes]:
        response = await self._aiohttp_client_session.get(url)
        # A failed download responds with an error body in place of the resource's
        # bytes. Those bytes are streamed straight into the caller's output file, so
        # without this check the error document itself is what gets saved as the
        # downloaded resource.
        self._check_for_api_error_response(
            status_code=response.status,
            response_json=(
                await self._read_response_json(response)
                if response.status >= 400
                else None
            ),
        )
        async for chunk in response.content.iter_chunked(maximum_chunk_size):
            yield chunk

    @staticmethod
    def _build_event_log_params(
        limit: int | None,
        offset: int | None,
    ) -> dict[str, JsonValue]:
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return params

    @staticmethod
    async def _read_response_json(response: aiohttp.ClientResponse) -> Any:
        # An error response is not guaranteed to carry a JSON body (the server returns
        # an empty body for the 401s it disguises, and an intermediary can return a
        # non-JSON body of its own), so an unparseable body is reported as no body
        # rather than raised over the top of the real error.
        try:
            return await response.json()
        except (aiohttp.ContentTypeError, ValueError):
            return None

    @staticmethod
    def _check_for_api_error_response(
        status_code: int, response_json: JsonValue | None
    ) -> None:
        # The server wraps every error it raises in an `{"error": ...}` envelope, and
        # that envelope is what carries the useful error information back to the
        # operator. It is not what decides *whether* the request failed though: any
        # 4XX/5XX is an error even when the body is missing the envelope or missing
        # entirely, and returning such a body to the caller makes it treat a failed
        # request as a successful one and read result fields off the error payload.
        # Note that a successful response body can be a list, so the envelope is only
        # looked for on a mapping.
        error = response_json.get("error") if isinstance(response_json, dict) else None

        if error is not None:
            raise RestAPIOperationError(
                status_code=status_code,
                code=error["code"],
                message=error["message"],
                detail=error["detail"],
            )

        # Empty bodies (HTTP 204 or 202 responses) reach here and are only an error if
        # the status says so.
        if status_code >= 400:
            raise RestAPIOperationError(
                status_code=status_code,
                code="UNEXPECTED_ERROR_RESPONSE",
                message=(
                    "Failed to perform the requested operation. The server returned an "
                    f"unexpected HTTP {status_code} response."
                ),
                detail={"response_body": response_json},
            )

    def _log_request_and_response(
        self,
        method: str,
        url: str,
        response: aiohttp.ClientResponse,
        response_json: dict[str, JsonValue],
    ):
        _http_response_code_to_color_string_map = {
            1: "<bold><cyan>",
            2: "<bold><green>",
            3: "<bold><cyan>",
            4: "<bold><yellow>",
            5: "<bold><red>",
        }
        color_string = _http_response_code_to_color_string_map[response.status // 100]
        format_string = (
            "<bold><blue>{}</></> {} " + color_string + "{} {}" + "</></> " + "{} {}"
        )
        self._logger.opt(colors=True).debug(
            format_string,
            method.upper(),
            url,
            response.status,
            response.reason,
            response.content_length,
            response_json,
        )

    async def _make_api_request(self, method: str, url: str, *args, **kwargs) -> Any:
        response = await self._aiohttp_client_session.request(
            method,
            url,
            *args,
            **kwargs,
        )

        # If we are logged in we should always expect a JSON response. The only time we
        # dont get a valid JSON response while logged in is when the server returns a
        # 401 Unauthorized due to invalid credentials during login or an expired user
        # session. Because the interpreters only expect RestAPIOperationError
        # exceptions for API errors, we construct and raise that exception here
        if response.status == 401:
            raise RestAPIOperationError(
                status_code=response.status,
                code="UNAUTHORIZED_ERROR",
                message=(
                    "Failed to perform the requested operation. The current client "
                    "session was unexpectedly logged out. Log in again to continue."
                ),
                detail=None,
            ) from None

        response_json = await self._read_response_json(response)
        self._log_request_and_response(
            method=method,
            url=url,
            response=response,
            response_json=response_json,
        )
        self._check_for_api_error_response(
            status_code=response.status, response_json=response_json
        )
        return response_json
