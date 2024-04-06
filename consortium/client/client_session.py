import uuid
from datetime import datetime
from typing import Any

import aiohttp

from consortium.client.client_exceptions import (
    AlreadyLoggedInError,
    FailedToLoginError,
    NotLoggedInError,
)
from consortium.client.objects.client_objects import ClientConfig


def _check_for_exceptions(func):
    async def wrapper(*args, **kwargs):
        response = await func(*args, **kwargs)

        if "error" in response:
            raise Exception(
                f"{response["error"]["code"]}: {response["error"]["message"]} ({response["error"]["detail"]})",
            )

        return response

    return wrapper


class ClientSession:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

        self.name = ""
        self.datetime_connected = datetime.now()
        self.client_session_id = uuid.uuid4()
        self._api_base_url = f"http://{self.client_config.remote_host}:{self.client_config.remote_port}/api"

        self._logged_in = False

    # Wrapper methods for the /api/server API endpoint.
    @_check_for_exceptions
    async def get_server_release(self) -> dict[str, Any]:
        server_release = await (
            await self.authorized_session.get(
                f"{self._api_base_url}/server/release",
            )
        ).json()
        return server_release

    # Wrapper methods for the /api/listener-templates API endpoint.
    @_check_for_exceptions
    async def get_all_listener_templates(self) -> list[dict[str, Any]]:
        all_listener_templates = await (
            await self.authorized_session.get(
                f"{self._api_base_url}/listener-templates/all",
            )
        ).json()
        return all_listener_templates

    @_check_for_exceptions
    async def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> dict[str, Any]:
        listener_template = await (
            await self.authorized_session.get(
                f"{self._api_base_url}/listener-templates/{listener_template_id}",
            )
        ).json()
        return listener_template

    # Wrapper methods for the /api/listeners API endpoint.
    @_check_for_exceptions
    async def get_all_listeners(self) -> list[dict[str, Any]]:
        all_listeners = await (
            await self.authorized_session.get(
                f"{self._api_base_url}/listeners/all",
            )
        ).json()
        return all_listeners

    @_check_for_exceptions
    async def get_listener_by_listener_id(
        self,
        listener_id: str,
    ) -> dict[str, Any]:
        listener = await (
            await self.authorized_session.get(
                f"{self._api_base_url}/listeners/{listener_id}",
            )
        ).json()
        return listener

    # Wrapper methods for the /api/users API endpoint.
    @_check_for_exceptions
    async def get_user_info_by_user_id(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        user = await (
            await self.authorized_session.get(
                f"{self._api_base_url}/users/{user_id}",
            )
        ).json()
        return user

    @_check_for_exceptions
    async def get_own_user_info(self) -> dict[str, Any]:
        user = await (
            await self.authorized_session.get(
                f"{self._api_base_url}/users/me",
            )
        ).json()
        return user

    @_check_for_exceptions
    async def get_all_users_info(self) -> list[dict[str, Any]]:
        all_users = await (
            await self.authorized_session.get(
                f"{self._api_base_url}/users/all",
            )
        ).json()
        return all_users

    # Wrapper methods for the /api/login API endpoint.
    async def login(self):
        if self._logged_in:
            raise AlreadyLoggedInError

        self._session = aiohttp.ClientSession()
        try:
            response = await self._session.post(
                f"http://{self.client_config.remote_host}:{self.client_config.remote_port}/api/login",
                data={
                    "username": self.client_config.username,
                    "password": self.client_config.password,
                },
            )
            token = (await response.json())["access_token"]
            self._session.headers.update({"Authorization": f"Bearer {token}"})
            self._logged_in = True
        except (aiohttp.ClientResponseError, KeyError) as exc:
            raise FailedToLoginError(str(exc))

    # Wrapper methods for the /api/login logout endpoint.
    async def logout(self):
        if not self._logged_in:
            raise NotLoggedInError

        await self._session.post(
            f"http://{self.client_config.remote_host}:{self.client_config.remote_port}/api/logout",
        )
        self._session.headers.pop("Authorization")
        await self._session.close()
        self._logged_in = False

    @property
    def authorized_session(self):
        if not self._logged_in:
            raise NotLoggedInError

        return self._session

    def __repr__(self) -> str:
        return f"ClientSession(client_config={self.client_config})"

    def __str__(self):
        return f'"{self.name}" ({self.client_session_id})'
