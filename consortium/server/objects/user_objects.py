import uuid
from datetime import datetime

import jwt

from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.server_jwt_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_EXPIRATION_DURATION,
    JSON_WEB_TOKEN_SECRET_KEY,
)


class JSONWebToken:
    def __init__(self):
        self.subject = uuid.uuid4()
        self.issued_at = datetime.now()
        self.expires = self.issued_at + JSON_WEB_TOKEN_EXPIRATION_DURATION
        self.access_token = jwt.encode(
            {
                "sub": str(self.subject),
                "iat": int(self.issued_at.timestamp()),
                "exp": int(self.expires.timestamp()),
            },
            JSON_WEB_TOKEN_SECRET_KEY,
            algorithm=JSON_WEB_TOKEN_ALGORITHMS[0],
        )

    def to_json(self):
        return {
            "access_token": self.access_token,
            "token_type": "bearer",
        }


class User:
    def __init__(self, user_account: UserAccountModel):
        self.user_account = user_account
        self.user_id = uuid.uuid4()
        self.display_name = user_account.username
        self.datetime_connected = datetime.now()
        self.datetime_last_active = self.datetime_connected
        self.json_web_token = JSONWebToken()

    @property
    def username(self) -> str:
        return self.user_account.username

    @property
    def role(self) -> str:
        return self.user_account.role

    def to_json(self):
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role,
            "user_account": {
                "user_account_id": str(self.user_account.user_account_id),
                "username": self.user_account.username,
            },
            "datetime_connected": self.datetime_connected,
            "datetime_last_active": self.datetime_last_active,
        }

    def __str__(self) -> str:
        return f"'{self.username}' ({self.user_id})"

    def __repr__(self) -> str:
        return f"User(user_account={self.user_account!r})"
