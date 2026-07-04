Since the events API lives on the same server as the REST API it is subject to the same
authorization requirements as the rest of the endpoints. This means that you will need
to include an `Authorization` header with a valid JWT token in order to make a
websocket connection to the events API.

To authenticate with the server, send a `POST` request to the `/api/login` endpoint
with a `username` and `password` parameter in the _request body_ to receive a JWT
token. The login mechanism uses [OAuth 2.0](https://oauth.net/2/) to authenticate users.
The response from the Oauth 2.0 authentication endpoint is standard and will look like
this:

```json title="OAuth 2.0 response"
{
  "access_token": "JWT",
  "token_type": "bearer"
}
```

Where `JWT` is the JSON Web Token as a string.

## Authenticating with the REST API

In the example below, we use the `requests` library to authenticate with the REST API
and receive a JSON Web Token.

```py title="print_jwt.py"
import requests # (1)

USERNAME = "admin" # (2)
PASSWORD = "admin"
AUTHORIZATION_URL = "http://localhost:9999/api/login"


def get_jwt(username: str, password: str, authorization_url: str) -> str:
    response = requests.post(
        authorization_url, data={"username": username, "password": password}
    )
    return response.json()["access_token"]


def main() -> None:
    jwt = get_jwt(
        username=USERNAME, password=PASSWORD, authorization_url=AUTHORIZATION_URL
    )
    print(jwt)


if __name__ == "__main__":
    main()
```

1. `requests` is a third party library, install it from
   [PyPI](https://pypi.org/project/requests/) with your preferred package manager of
   choice.
2. By default, the server binds at `0.0.0.0:9999` and includes an admin account with
   the username `admin` and password `admin`. Change these constants to fit your
   configuration appropriately.

If all goes well you should see the JSON Web Token printed to the console. It should
look like a long string of random alphanumeric characters with 3 distinct segments
separated with dots. Here's mine (don't bother, its already invalid now):

```plaintext title="What you should see in your terminal"
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5MGNkMmE1YS1jMGYyLTQ5OGUtYjljZC1hY2M5NzgxOGE5OWMiLCJpYXQiOjE3MjM0MjIyMjMsImV4cCI6MTcyMzUwODYyM30.fHSHPilgfR29D2Rpoyv6zX-FMqP88eJy-W1noIj0OCI
```

!!! warning
    The JSON web token is what controls your access to the events API. Even if someone
    were not to know your username and password, they could still access the events API
    (and **every other** API endpoint that you have the relevant permissions for) if
    they had your JWT token. **Keep it secure**.

## Connecting to the websocket endpoint

Now that you have a valid JSON Web Token you can connect to the websocket endpoint at
`ws://localhost:9999/api/events`. The initial request to that endpoint must be made
with the JSON Web Token present in the Authorization header.

!!! note
    The OAuth 2.0 format for including JSON Web Tokens in the Authorization header is
    to _precede_ the JSON Web Token with the string `Bearer ` (including the space)
    like so:

    ```plaintext title="Authorization header format"
    Authorization: Bearer JWT
    ```

The following example demonstrates how to connect to
the websocket endpoint using the `websockets` library. Remember to replace the `JWT`
constant with the JSON Web Token that was printed by the script in the previous section.

```py title="connect_to_ws.py"
import asyncio
import websockets

JWT = "YOUR_JWT" # (1)
EVENTS_API_URL = "ws://localhost:9999/api/events"


async def main():
    async with websockets.connect(
        EVENTS_API_URL, extra_headers={"Authorization": f"Bearer {JWT}"}
    ) as websocket:
        pass


if __name__ == "__main__":
    asyncio.run(main())
```

1. Replace `YOUR_JWT` with the JSON Web Token you received from the REST API.

You will receive no messages from the websocket endpoint until (at the very least) you
subscribe to an endpoint. So your script should just exit without doing anything. A
failed attempt will be met with a websocket exception claiming that the websocket
connection was rejected.

```plaintext title="Failed connection attempt"
websockets.exceptions.InvalidStatusCode: server rejected WebSocket connection: HTTP 403
```

[introduction.md](introduction.md)
If this happens, double-check your JSON Web Token and the URL you are connecting to. If
you want more information about what _exactly_ failed you have to start the server in
debug mode by running the server with the `-d` or `--debug` flag.

```shell title="Start the server in debug mode"
uv run python consortium.py -d
```

## Putting it all together

All together, the modified script to receive a JSON Web Token and then make a websocket
connection to the events API looks like this:

```py title="event_notifier.py"
import asyncio
import requests
import websockets

USERNAME = "admin"
PASSWORD = "admin"
AUTHORIZATION_URL = "http://localhost:9999/api/login"
EVENTS_API_URL = "ws://localhost:9999/api/events"


def get_jwt(username: str, password: str, authorization_url: str) -> str:
    response = requests.post(
        authorization_url,
        data={"username": username, "password": password},
    )
    return response.json()["access_token"]


async def main():
    jwt = get_jwt(
        username=USERNAME,
        password=PASSWORD,
        authorization_url=AUTHORIZATION_URL,
    )
    async with websockets.connect(
        EVENTS_API_URL, extra_headers={"Authorization": f"Bearer {jwt}"}
    ) as websocket:
        pass


if __name__ == "__main__":
    asyncio.run(main())
```

We will be building off of this script to make a basic event notification system.
