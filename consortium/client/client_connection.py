from datetime import datetime
from typing import Any

import aiohttp

from consortium.client.client_exceptions import (
    AlreadyLoggedInError,
    APIError,
    FailedToLoginError,
    InvalidServerLoginResponseError,
    NotLoggedInError,
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
            raise APIError(
                f"{response["error"]["code"]}: {response["error"]["message"]} (Detail: {response["error"]["detail"]})",
            )
        elif "error" in response and not response["error"]["detail"]:
            raise APIError(
                f"{response["error"]["code"]}: {response["error"]["message"]}",
            )

        return response

    return wrapper


class ClientConnection:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config
        self.datetime_connected = None

        self._api_base_url = f"http://{self.client_config.remote_host}:{self.client_config.remote_port}/api"
        self._aiohttp_client_session = aiohttp.ClientSession()
        self._logged_in = False

    # All client connections should be closed when the client is done with them.
    async def close(self):
        await self._aiohttp_client_session.close()

    # Wrapper methods for the /api/login API endpoints.
    async def login(self):
        if self._logged_in:
            raise AlreadyLoggedInError(
                "Client is already logged in to server (Log out from server before attempting to log in).",
            )

        response = await self._aiohttp_client_session.post(
            f"{self._api_base_url}/login",
            data={
                "username": self.client_config.username,
                "password": self.client_config.password,
            },
        )
        response_json = await response.json()

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
