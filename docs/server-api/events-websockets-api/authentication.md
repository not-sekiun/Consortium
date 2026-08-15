Since the events API lives on the same server as the REST API it is subject to the same
authorization requirements as the rest of the endpoints. A websocket handshake cannot
carry those credentials the same way though: the browser `WebSocket` constructor has no
option for request headers, so a JSON Web Token cannot travel in an `Authorization`
header on the connection request the way it does on every REST call.

Connecting to the events API therefore takes three steps:

1. `POST /api/login` with your credentials to receive a JSON Web Token.
2. `POST /api/ws/ticket` with that token in the `Authorization` header to receive a
   short-lived, single-use **ticket**.
3. Open the websocket with the ticket in the query string:
   `ws://localhost:9999/api/ws/events?ticket=TICKET`.

The ticket is the handshake's only credential. An `Authorization` header sent on a
handshake is ignored entirely, and a handshake without a ticket is rejected.

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

## Obtaining a websocket ticket

A ticket is exchanged for over ordinary HTTP, where the JSON Web Token travels in the
`Authorization` header as usual. Send a `POST` request to `/api/ws/ticket`. The endpoint
takes **no request body and no user identifier**: a ticket is always minted for the
calling token's own session, so there is no shape of request that asks for somebody
else's.

```json title="Response from /api/ws/ticket"
{
  "ticket": "TICKET",
  "time_to_live_seconds": 30
}
```

| Field                  | Description                                                     |
|------------------------|-----------------------------------------------------------------|
| `ticket`               | The opaque ticket string to present on the handshake.           |
| `time_to_live_seconds` | How long the ticket stays redeemable for, in seconds.           |

The ticket is opaque: it encodes nothing about your token or your account, and neither
can be derived from it. Three properties govern how you use one:

- **Single use.** A ticket authenticates exactly one handshake and is spent the moment
  the server redeems it. Every connection needs its own ticket, including a reconnect
  after a dropped connection and each of several connections opened at once.
- **Short-lived.** The ticket expires shortly after issue. Read the window from
  `time_to_live_seconds` rather than hardcoding it, and obtain the ticket immediately
  before connecting rather than holding one for later.
- **Bound to your session.** The ticket names the session that asked for it, so the
  connection it opens is that session's. Logging out invalidates any ticket issued to
  that session, whether or not it has expired.

!!! note
    Issuing a ticket requires the `USE_EVENTS_WEBSOCKET` permission, the same permission
    the websocket endpoint itself checks. Obtaining a ticket is therefore never a way
    around that check. See
    [Roles and Permissions](../../server-usage/roles-and-permissions.md).

Two failures are worth handling on this endpoint:

| Status | Meaning                                                                          |
|--------|----------------------------------------------------------------------------------|
| `429`  | The endpoint's rate limit has been tripped. Back off and retry.                  |
| `503`  | The server is holding too many outstanding tickets and cannot issue more right now. Retry in a moment. |

The endpoint is rate limited to 20 requests per minute per client address. A client
needs exactly one ticket per handshake, so only page reloads and reconnect attempts
spend from that budget and normal use never approaches it. A reconnect loop that retries
without backing off will.

!!! warning
    A ticket is a credential, and unlike the JSON Web Token it travels in a **URL**.
    URLs are logged in far more places than headers are (proxies, access logs, browser
    history), so treat a ticket as sensitive: never log it, never persist it, and never
    reuse one. Its short life is what bounds the damage of a leaked ticket, which is
    why the window is deliberately tight.

## Connecting to the websocket endpoint

With a ticket in hand you can connect to the websocket endpoint at
`ws://localhost:9999/api/ws/events`, passing the ticket as the `ticket` query parameter.

```py title="connect_to_ws.py"
import asyncio
import websockets

TICKET = "YOUR_TICKET" # (1)
EVENTS_API_URL = "ws://localhost:9999/api/ws/events"


async def main():
    async with websockets.connect(f"{EVENTS_API_URL}?ticket={TICKET}") as websocket:
        pass


if __name__ == "__main__":
    asyncio.run(main())
```

1. Replace `YOUR_TICKET` with a ticket obtained from `/api/ws/ticket`. Tickets expire
   within seconds, so in practice you obtain one in the same script that connects
   rather than pasting one in. See [putting it all together](#putting-it-all-together)
   below.

You will receive no messages from the websocket endpoint until (at the very least) you
subscribe to an endpoint. So your script should just exit without doing anything. A
failed attempt will be met with a websocket exception claiming that the websocket
connection was rejected.

```plaintext title="Failed connection attempt"
websockets.exceptions.InvalidStatus: server rejected WebSocket connection: HTTP 403
```

The server deliberately gives no reason for a refusal. A ticket that was never issued,
one that has expired, and one that has already been redeemed are all rejected
identically, so that the handshake cannot be used to probe which of the three is the
case. If this happens, the likely causes in order are: the ticket was already spent on
an earlier connection, too long passed between obtaining it and connecting, the session
the ticket was issued for has since logged out, or the URL is wrong. If you want more
information about what _exactly_ failed you have to start the server in debug mode by
running the server with the `-d` or `--debug` flag.

```shell title="Start the server in debug mode"
uv run python consortium.py -d
```

## Putting it all together

All together, the script to receive a JSON Web Token, exchange it for a ticket, and then
make a websocket connection to the events API looks like this:

```py title="event_notifier.py"
import asyncio
import requests
import websockets

USERNAME = "admin"
PASSWORD = "admin"
AUTHORIZATION_URL = "http://localhost:9999/api/login"
TICKET_URL = "http://localhost:9999/api/ws/ticket"
EVENTS_API_URL = "ws://localhost:9999/api/ws/events"


def get_jwt(username: str, password: str, authorization_url: str) -> str:
    response = requests.post(
        authorization_url,
        data={"username": username, "password": password},
    )
    return response.json()["access_token"]


def get_ticket(jwt: str, ticket_url: str) -> str: # (1)
    response = requests.post(ticket_url, headers={"Authorization": f"Bearer {jwt}"})
    response.raise_for_status()
    return response.json()["ticket"]


async def main():
    jwt = get_jwt(
        username=USERNAME,
        password=PASSWORD,
        authorization_url=AUTHORIZATION_URL,
    )
    ticket = get_ticket(jwt=jwt, ticket_url=TICKET_URL)

    async with websockets.connect(f"{EVENTS_API_URL}?ticket={ticket}") as websocket:
        pass


if __name__ == "__main__":
    asyncio.run(main())
```

1. Call this once per connection, immediately before connecting. Holding the returned
   ticket, or reusing it for a second connection, gets that connection rejected.

We will be building off of this script to make a basic event notification system.
