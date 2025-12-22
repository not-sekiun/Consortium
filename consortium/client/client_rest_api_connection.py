from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import IO, Any, Literal

import aiohttp
from loguru import logger

from consortium.client.exceptions.client_rest_api_connection_exceptions import (
    ClientRESTAPIConnectionAlreadyLoggedInError,
    ClientRESTAPIConnectionFailedToLoginError,
    ClientRESTAPIConnectionNotLoggedInError,
    ClientRESTAPIOperationError,
    InvalidServerRESTAPILoginResponseError,
)


def _requires_authentication(
    async_func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def wrapper(self, *args, **kwargs) -> Any:
        if not self.logged_in:
            raise ClientRESTAPIConnectionNotLoggedInError

        return await async_func(self, *args, **kwargs)

    return wrapper


# TODO: Consider transitioning to auto generation of client code using OpenAPI
#    specifications once the API stabilizes. Figure out how to not have the API be name
#    mangled.
class ClientRESTAPIConnection:
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

        self._client_rest_api_connection_logger = logger.bind(
            logger_name=(str(self)),
        )
        self._api_base_url = f"http://{self.remote_host}:{self.remote_port}/api"
        self._aiohttp_client_session = None

    def __str__(self) -> str:
        return (
            f"Client REST API connection to {self.remote_host}:{self.remote_port} as "
            f"'{self.username}'"
        )

    def __repr__(self) -> str:
        return (
            f"ClientRESTAPIConnection(username={self.username!r}, "
            f"password={self.password!r}, remote_host={self.remote_host!r}, "
            f"remote_port={self.remote_port!r})"
        )

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self) -> None:
        if self.logged_in:
            raise ClientRESTAPIConnectionAlreadyLoggedInError
        try:
            self._aiohttp_client_session = aiohttp.ClientSession()
            response = await self._aiohttp_client_session.post(
                f"{self._api_base_url}/login",
                data={
                    "username": self.username,
                    "password": self.password,
                },
            )
            response_json = await response.json()
        except Exception as exc:
            # Close the client session if an exception is raised while attempting to log
            # in to the server.
            await self._aiohttp_client_session.close()
            raise exc

        if response.status != 200:
            raise ClientRESTAPIConnectionFailedToLoginError
        if (
            response_json["token_type"] != "bearer"
            or "access_token" not in response_json
        ):
            raise InvalidServerRESTAPILoginResponseError

        self.json_web_token = response_json["access_token"]
        self._aiohttp_client_session.headers.update(
            {"Authorization": f"Bearer {response_json['access_token']}"},
        )
        self.logged_in = True

    async def disconnect(self) -> None:
        if not self.logged_in:
            raise ClientRESTAPIConnectionNotLoggedInError

        await self.logout()
        self._aiohttp_client_session.headers.pop("Authorization")
        await self._aiohttp_client_session.close()
        self.logged_in = False

    # Wrapper methods for the /api/login API endpoints.
    async def login(self, username: str, password: str) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/login",
            data={
                "username": username,
                "password": password,
            },
        )

    # Wrapper methods for the /api/logout API endpoint.
    @_requires_authentication
    async def logout(self) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/logout",
        )

    # Wrapper methods for the /api/server API endpoints.
    @_requires_authentication
    async def get_server_release(self) -> dict[str, Any]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/server/release",
        )

    @_requires_authentication
    async def get_server_config(self) -> dict[str, Any]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/server/config",
        )

    # Wrapper methods for the /api/listener-templates API endpoint.
    @_requires_authentication
    async def get_all_listener_templates(self) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/listener-templates/all",
        )

    @_requires_authentication
    async def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/listener-templates/{listener_template_id}",
        )

    @_requires_authentication
    async def create_listener_through_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
        listener_template_option_values: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/listener-templates/{listener_template_id}",
            json=listener_template_option_values,
        )

    # Wrapper methods for the /api/listeners API endpoint.
    @_requires_authentication
    async def get_all_listeners(self) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/listeners/all",
        )

    @_requires_authentication
    async def get_listener_by_listener_id(
        self,
        listener_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/listeners/{listener_id}",
        )

    @_requires_authentication
    async def update_listener_by_listener_id(
        self,
        listener_id: str,
        new_listener_attributes: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._make_request(
            method="PATCH",
            url=f"{self._api_base_url}/listeners/{listener_id}",
            json=new_listener_attributes,
        )

    @_requires_authentication
    async def delete_listener_by_listener_id(
        self,
        listener_id: str,
    ):
        return await self._make_request(
            method="DELETE",
            url=f"{self._api_base_url}/listeners/{listener_id}",
        )

    @_requires_authentication
    async def start_listener_by_listener_id(self, listener_id: str) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/listeners/{listener_id}/start",
        )

    @_requires_authentication
    async def stop_listener_by_listener_id(self, listener_id: str) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/listeners/{listener_id}/stop",
        )

    @_requires_authentication
    async def cancel_listener_by_listener_id(self, listener_id: str) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/listeners/{listener_id}/cancel",
        )

    # Wrapper methods for the /api/agent-templates API endpoint.
    @_requires_authentication
    async def get_all_agent_templates(self) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agent-templates/all",
        )

    @_requires_authentication
    async def get_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agent-templates/{agent_template_id}",
        )

    @_requires_authentication
    async def create_agent_generator_through_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
        agent_template_option_values: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/agent-templates/{agent_template_id}",
            json=agent_template_option_values,
        )

    # Wrapper methods for the /api/agent-generators API endpoint.
    @_requires_authentication
    async def get_all_agent_generators(self) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agent-generators/all",
        )

    @_requires_authentication
    async def get_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}",
        )

    @_requires_authentication
    async def update_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
        new_agent_generator_attributes: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._make_request(
            method="PATCH",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}",
            json=new_agent_generator_attributes,
        )

    @_requires_authentication
    async def delete_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="DELETE",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}",
        )

    @_requires_authentication
    async def start_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}/start",
        )

    @_requires_authentication
    async def stop_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}/stop",
        )

    @_requires_authentication
    async def cancel_agent_generator_by_agent_generator_id(
        self,
        agent_generator_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/agent-generators/{agent_generator_id}/cancel",
        )

    # Wrapper methods for the /api/agents API endpoint.
    @_requires_authentication
    async def get_all_agents(self) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/all",
        )

    @_requires_authentication
    async def get_agent_by_agent_id(self, agent_id: str) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}",
        )

    @_requires_authentication
    async def get_all_agent_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/tasks",
        )

    @_requires_authentication
    async def get_all_queued_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/tasks/queued",
        )

    @_requires_authentication
    async def get_all_running_agent_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/tasks/running",
        )

    @_requires_authentication
    async def get_all_completed_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/tasks/completed",
        )

    @_requires_authentication
    def get_agent_task_by_agent_id_and_task_id(
        self,
        agent_id: str,
        task_id: str,
    ):
        return self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/tasks/{task_id}",
        )

    @_requires_authentication
    async def get_all_agent_results_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/results",
        )

    @_requires_authentication
    async def get_all_successful_agent_results_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/results/success",
        )

    @_requires_authentication
    async def get_all_failed_agent_results_by_agent_id(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/results/fail",
        )

    @_requires_authentication
    def get_agent_result_by_agent_id_and_result_id(
        self,
        agent_id: str,
        result_id: str,
    ):
        return self._make_request(
            method="GET",
            url=f"{self._api_base_url}/agents/{agent_id}/results/{result_id}",
        )

    @_requires_authentication
    async def update_agent_by_agent_id(
        self,
        agent_id: str,
        new_agent_attributes: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._make_request(
            method="PATCH",
            url=f"{self._api_base_url}/agents/{agent_id}",
            json=new_agent_attributes,
        )

    # Wrapper methods for the /api/users API endpoint.
    @_requires_authentication
    async def get_user_info_by_user_id(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/users/{user_id}",
        )

    @_requires_authentication
    async def get_own_user_info(self) -> dict[str, Any]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/users/me",
        )

    @_requires_authentication
    async def get_all_users_info(self) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/users/all",
        )

    @_requires_authentication
    async def task_agent_by_agent_id(
        self,
        agent_id: str,
        command: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._make_request(
            method="POST",
            url=f"{self._api_base_url}/agents/{agent_id}/tasks",
            json={"command": command, "arguments": arguments},
        )

    # Wrapper methods for the /api/assets API endpoint.
    async def get_all_assets(
        self,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/assets/all",
        )

    # Wrapper methods for the /api/assets API endpoint.
    async def get_asset_by_asset_id(
        self,
        asset_id: str,
    ) -> list[dict[str, Any]]:
        return await self._make_request(
            method="GET",
            url=f"{self._api_base_url}/assets/{asset_id}",
        )

    async def download_asset_by_asset_id(
        self,
        asset_id: str,
        maximum_chunk_size: int = 1024,
    ) -> AsyncGenerator[bytes, None, None]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/assets/download/{asset_id}",
        )
        async for chunk in response.content.iter_chunked(maximum_chunk_size):
            yield chunk

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
    ) -> dict[str, Any]:
        response = await self._aiohttp_client_session.post(
            f"{self._api_base_url}/assets/upload",
            data={
                "file": file_object,
                "is_directory": str(is_directory).lower(),
                "name": name,
                "description": description,
                "asset_directory_archive_file_format": ""
                if asset_directory_archive_file_format is None
                else asset_directory_archive_file_format,
            },
        )
        return await response.json()

    @staticmethod
    def _check_for_rest_api_error_response(
        response_json: dict[str, Any],
    ) -> None:
        if "error" in response_json and response_json["error"]["detail"]:
            raise ClientRESTAPIOperationError(
                f"{response_json['error']['code']}: "
                f"{response_json['error']['message']} "
                f"(Detail: {response_json['error']['detail']})",  # TODO: Consider formatting this more nicely
            )
        elif "error" in response_json and not response_json["error"]["detail"]:
            raise ClientRESTAPIOperationError(
                f"{response_json['error']['code']}: "
                f"{response_json['error']['message']}",
            )

    def _log_request_and_response(
        self,
        method: str,
        url: str,
        response: aiohttp.ClientResponse,
        response_json: dict[str, Any],
    ):
        _http_response_code_to_color_string_map = {
            1: "<bold><blue>",
            2: "<bold><green>",
            3: "<bold><blue>",
            4: "<bold><yellow>",
            5: "<bold><red>",
        }
        color_string = _http_response_code_to_color_string_map[response.status // 100]
        format_string = (
            "<bold><blue>{}</></> {} " + color_string + "{} {}" + "</></> " + "{} {}"
        )
        self._client_rest_api_connection_logger.opt(colors=True).debug(
            format_string,
            method.upper(),
            url,
            response.status,
            response.reason,
            response.content_length,
            response_json,
        )

    async def _make_request(self, method: str, url: str, *args, **kwargs) -> Any:
        response = await self._aiohttp_client_session.request(
            method,
            url,
            *args,
            **kwargs,
        )
        response_json = await response.json()
        self._log_request_and_response(
            method=method,
            url=url,
            response=response,
            response_json=response_json,
        )
        self._check_for_rest_api_error_response(response_json=response_json)
        return response_json
