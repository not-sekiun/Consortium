import uuid
from datetime import datetime
from typing import Any

import aiohttp
from loguru import logger

from consortium.client.client_exceptions import (
    AlreadyLoggedInError,
    FailedToLoginError,
    InvalidServerLoginResponseError,
    NotLoggedInError,
    RESTAPIError,
)
from consortium.client.objects.client_objects import ClientConfig


def _check_if_logged_in(async_func):
    async def wrapper(*args, **kwargs):
        # args[0] is the self parameter of the method.
        if not args[0]._logged_in:
            raise NotLoggedInError(
                "Client is not logged in to server.",
            )

        return await async_func(*args, **kwargs)

    return wrapper


def _check_for_rest_api_error_response(async_func):
    async def wrapper(*args, **kwargs):
        response = await async_func(*args, **kwargs)

        if "error" in response and response["error"]["detail"]:
            raise RESTAPIError(
                f"{response["error"]["code"]}: {response["error"]["message"]} "
                f"(Detail: {response["error"]["detail"]})",
            )
        elif "error" in response and not response["error"]["detail"]:
            raise RESTAPIError(
                f"{response["error"]["code"]}: {response["error"]["message"]}",
            )

        return response

    return wrapper


class ClientConnection:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config
        self.username = client_config.username
        self.password = client_config.password
        self.remote_host = client_config.remote_host
        self.remote_port = client_config.remote_port

        self.name = ""
        self.datetime_connected = None
        self.client_connection_id = uuid.uuid4()

        self._client_connection_logger = logger.bind(
            logger_name=f'Consortium Client Connection "{self.name}" ({self.client_connection_id})',
        )
        self._api_base_url = f"http://{self.remote_host}:{self.remote_port}/api"
        self._logged_in = False

    async def _request(self, method: str, url: str, **kwargs) -> Any:
        response = await self._aiohttp_client_session.request(method, url, **kwargs)
        response_json = await response.json()

        color_map = {
            "1": ("<bold><blue>", "</></>"),
            "2": ("<bold><green>", "</></>"),
            "3": ("<bold><blue>", "</></>"),
            "4": ("<bold><yellow>", "</></>"),
            "5": ("<bold><red>", "</></>"),
        }
        if kwargs:
            format_string = (
                "<bold><blue>{}</></> {} {}"
                + color_map[str(response.status)[0]][0]
                + " {} {}"
                + color_map[str(response.status)[0]][1]
                + " {} {}"
            )
            self._client_connection_logger.opt(ansi=True).debug(
                format_string,
                method.upper(),
                url,
                kwargs,
                response.status,
                response.reason,
                response.content_length,
                response_json,
            )
        else:
            format_string = (
                "<bold><blue>{}</></> {}"
                + color_map[str(response.status)[0]][0]
                + " {} {}"
                + color_map[str(response.status)[0]][1]
                + " {} {}"
            )
            self._client_connection_logger.opt(ansi=True).debug(
                format_string,
                method.upper(),
                url,
                response.status,
                response.reason,
                response.content_length,
                response_json,
            )

        return response_json

    # Wrapper methods for the /api/login API endpoints.
    async def login(self):
        if self._logged_in:
            raise AlreadyLoggedInError(
                "Client is already logged in to server (Log out from server before "
                "attempting to log in).",
            )

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
            raise FailedToLoginError(
                "Failed to login to server. Either invalid credentials were provided "
                "or the server is not a valid Consortium server instance.",
            )
        if (
            response_json["token_type"] != "bearer"
            or "access_token" not in response_json
        ):
            raise InvalidServerLoginResponseError(
                "Failed to login to server because it did not return a valid OAuth2 "
                "JSON web token. The server is likely not a valid Consortium server "
                "instance.",
            )

        self.datetime_connected = datetime.now()
        self._aiohttp_client_session.headers.update(
            {"Authorization": f"Bearer {response_json['access_token']}"},
        )
        self._logged_in = True

    # Wrapper methods for the /api/logout API endpoint.
    async def logout(self):
        if not self._logged_in:
            raise NotLoggedInError("Client is not logged in to server.")

        await self._request(
            method="POST",
            url=f"{self._api_base_url}/logout",
        )
        self._aiohttp_client_session.headers.pop("Authorization")
        await self._aiohttp_client_session.close()
        self._logged_in = False

    # Wrapper methods for the /api/server API endpoints.
    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_server_release(self) -> dict[str, Any]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/server/release",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_server_config(self) -> dict[str, Any]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/server/config",
        )

    # Wrapper methods for the /api/listener-templates API endpoint.
    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_all_listener_templates(self) -> list[dict[str, Any]]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/listener-templates/all",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/listener-templates/{listener_template_id}",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def create_listener_through_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
        listener_template_option_values: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            url=f"{self._api_base_url}/listener-templates/{listener_template_id}",
            json=listener_template_option_values,
        )

    # Wrapper methods for the /api/agent-generators API endpoint.
    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_all_agent_generators(self) -> list[dict[str, Any]]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/agent-generators/all",
        )

    # Wrapper methods for the /api/agent-templates API endpoint.
    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_all_agent_templates(self) -> list[dict[str, Any]]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/agent-templates/all",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/agent-templates/{agent_template_id}",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def create_agent_generator_through_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
        agent_template_option_values: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            url=f"{self._api_base_url}/agent-templates/{agent_template_id}",
            json=agent_template_option_values,
        )

    # Wrapper methods for the /api/listeners API endpoint.
    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_all_listeners(self) -> list[dict[str, Any]]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/listeners/all",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_listener_by_listener_id(
        self,
        listener_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/listeners/{listener_id}",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def start_listener_by_listener_id(self, listener_id: str) -> dict[str, Any]:
        return await self._request(
            method="POST",
            url=f"{self._api_base_url}/listeners/{listener_id}/start",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def stop_listener_by_listener_id(self, listener_id: str) -> dict[str, Any]:
        return await self._request(
            method="POST",
            url=f"{self._api_base_url}/listeners/{listener_id}/stop",
        )

    # Wrapper methods for the /api/users API endpoint.
    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_user_info_by_user_id(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/users/{user_id}",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_own_user_info(self) -> dict[str, Any]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/users/me",
        )

    @_check_if_logged_in
    @_check_for_rest_api_error_response
    async def get_all_users_info(self) -> list[dict[str, Any]]:
        return await self._request(
            method="GET",
            url=f"{self._api_base_url}/users/all",
        )

    def __repr__(self) -> str:
        return f"ClientConnection(client_config={self.client_config})"

    def __str__(self):
        return f'"{self.name}" ({self.client_connection_id})'
