import uuid
from datetime import datetime

import jwt

from consortium.server.server_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_EXPIRATION_DURATION,
    JSON_WEB_TOKEN_SECRET_KEY,
)


class _JSONWebToken:
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
    def __init__(
        self,
        username: str,
        password: str,
        role: str,
        remote_host: str,
    ):
        self.username = username
        self.password = password
        self.role = role
        self.json_web_token = _JSONWebToken()
        self.remote_host = remote_host
        self.datetime_connected = datetime.now()
        self.user_id = uuid.uuid4()

    def to_json(self):
        return {
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "json_web_token": self.json_web_token.to_json(),
            "remote_host": self.remote_host,
            "datetime_connected": self.datetime_connected,
            "user_id": str(self.user_id),
        }

    def __str__(self) -> str:
        return f'"{self.username}" ({self.user_id})'

    def __repr__(self) -> str:
        return (
            f"User(username={self.username!r}, password={self.password!r}, "
            f"role={self.role!r}, remote_host={self.remote_host!r}, "
            f"datetime_connected={self.datetime_connected!r}, user_id={self.user_id!r})"
        )
