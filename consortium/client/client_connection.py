import uuid
from datetime import datetime
from typing import Any

import aiohttp

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
                "Client is not logged in to server (Log in to server before attempting to make an API request).",
            )

        return await async_func(*args, **kwargs)

    return wrapper


def _check_for_api_error_response(async_func):
    async def wrapper(*args, **kwargs):
        response = await async_func(*args, **kwargs)

        if "error" in response and response["error"]["detail"]:
            raise RESTAPIError(
                f"{response["error"]["code"]}: {response["error"]["message"]} (Detail: {response["error"]["detail"]})",
            )
        elif "error" in response and not response["error"]["detail"]:
            raise RESTAPIError(
                f"{response["error"]["code"]}: {response["error"]["message"]}",
            )

        return response

    return wrapper


# TODO: Add debug messages for API requests.
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

        self._api_base_url = f"http://{self.remote_host}:{self.remote_port}/api"
        self._logged_in = False

    # Wrapper methods for the /api/login API endpoints.
    async def login(self):
        if self._logged_in:
            raise AlreadyLoggedInError(
                "Client is already logged in to server (Log out from server before attempting to log in).",
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
                "Failed to login to server (Either invalid credentials were provided or the server is not a valid Consortium server instance).",
            )
        if (
            response_json["token_type"] != "bearer"
            or "access_token" not in response_json
        ):
            raise InvalidServerLoginResponseError(
                "Failed to login to server because it did not return a valid OAuth2 JSON web token (The server is likely not a valid Consortium server instance).",
            )

        self.datetime_connected = datetime.now()
        self._aiohttp_client_session.headers.update(
            {"Authorization": f"Bearer {response_json['access_token']}"},
        )
        self._logged_in = True

    # Wrapper methods for the /api/logout API endpoint.
    async def logout(self):
        if not self._logged_in:
            raise NotLoggedInError(
                "Client is not logged in to server (Log in to server before attempting to log out).",
            )

        await self._aiohttp_client_session.post(
            f"{self._api_base_url}/logout",
        )
        self._aiohttp_client_session.headers.pop("Authorization")
        await self._aiohttp_client_session.close()
        self._logged_in = False

    # Wrapper methods for the /api/server API endpoints.
    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_server_release(self) -> dict[str, Any]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/server/release",
        )
        return await response.json()

    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_server_config(self) -> dict[str, Any]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/server/config",
        )
        return await response.json()

    # Wrapper methods for the /api/listener-templates API endpoint.
    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_all_listener_templates(self) -> list[dict[str, Any]]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/listener-templates/all",
        )
        return await response.json()

    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> dict[str, Any]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/listener-templates/{listener_template_id}",
        )
        return await response.json()

    # Wrapper methods for the /api/listeners API endpoint.
    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_all_listeners(self) -> list[dict[str, Any]]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/listeners/all",
        )
        return await response.json()

    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_listener_by_listener_id(
        self,
        listener_id: str,
    ) -> dict[str, Any]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/listeners/{listener_id}",
        )
        return await response.json()

    # Wrapper methods for the /api/users API endpoint.
    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_user_info_by_user_id(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/users/{user_id}",
        )
        return await response.json()

    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_own_user_info(self) -> dict[str, Any]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/users/me",
        )
        return await response.json()

    @_check_if_logged_in
    @_check_for_api_error_response
    async def get_all_users_info(self) -> list[dict[str, Any]]:
        response = await self._aiohttp_client_session.get(
            f"{self._api_base_url}/users/all",
        )
        return await response.json()

    def __repr__(self) -> str:
        return f"ClientConnection(client_config={self.client_config})"

    def __str__(self):
        return f'"{self.name}" ({self.client_connection_id})'
