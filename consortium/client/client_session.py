import json
import uuid

import aiohttp

from consortium.client.client_config import CONSORTIUM_RELEASE_JSON_FILE_PATH
from consortium.client.client_exceptions import (
    AlreadyLoggedInError,
    FailedToLoginError,
    NotLoggedInError,
)
from consortium.client.objects.client_objects import ClientConfig, ClientRelease


class ClientSession:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

        # Load client release file
        with open(str(CONSORTIUM_RELEASE_JSON_FILE_PATH), "r") as file:
            release = file.read()
        json_release = json.loads(release)
        self.client_release = ClientRelease(**json_release)
        self.session_id = uuid.uuid4()
        self.api_url = f"http://{self.client_config.remote_host}:{self.client_config.remote_port}/api"

        self._session = aiohttp.ClientSession()
        self._logged_in = False

    async def login_session(self):
        if self._logged_in:
            raise AlreadyLoggedInError

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

    async def logout_session(self):
        if not self._logged_in:
            raise NotLoggedInError

        await self._session.post(
            f"http://{self.client_config.remote_host}:{self.client_config.remote_port}/api/logout",
        )
        self._session.headers.pop("Authorization")
        # TODO: Implement a way to close the session and then reuse the session object
        #  when logging in again after logging out.
        await self._session.close()
        self._logged_in = False

    @property
    def authorized_session(self):
        if not self._logged_in:
            raise NotLoggedInError

        return self._session
