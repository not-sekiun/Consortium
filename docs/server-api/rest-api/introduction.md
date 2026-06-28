The REST API is automatically documented using [OpenAPI](https://www.openapis.org/). By
default, the server binds at `http://localhost:9999`.

| URL                              | Description                        |
|----------------------------------|------------------------------------|
| `http://localhost:9999/docs`     | Swagger UI: interactive reference. |
| `http://localhost:9999/redoc`    | ReDoc: readable reference.         |

To prevent server fingerprinting or information leakage, the documentation pages are
**only accessible via `localhost`** external clients cannot access them.

!!! note
    The websocket events API is **not** covered here. See the
    [Events Websockets API](../events-websockets-api/introduction.md) documentation.

## Authentication

Most endpoints require a Bearer token. Obtain one by sending a `POST` request to
`/api/login` with your credentials as form data.

```json title="Response from /api/login"
{
  "access_token": "JWT",
  "token_type": "bearer"
}
```

To quickly retrieve a token from the command line:

=== "Bash"

    ```bash
    curl -s -X POST http://localhost:9999/api/login \
        -d "username=admin&password=admin" \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
    ```

=== "PowerShell"

    ```powershell
    (Invoke-RestMethod -Method Post -Uri "http://localhost:9999/api/login" -Body @{username="admin";password="admin"}).access_token
    ```

### Authorizing in Swagger UI

1. Open `http://localhost:9999/docs`.
2. Click the **Authorize** button (top right).
3. Input your `username` and `password` in the top 2 form fields you can ignore the
`client_id` and `client_secret`

All subsequent requests made through the UI will include the token automatically.

### Making authorized requests in code

The example below uses the [`requests`](https://pypi.org/project/requests/) library to
authenticate and build a session that automatically attaches the token to every request.

```py title="authorized_client.py"
import requests

USERNAME = "admin" # (1)
PASSWORD = "admin"
BASE_URL = "http://localhost:9999"


def make_authorized_session(username: str, password: str, base_url: str) -> requests.Session:
    response = requests.post(
        f"{base_url}/api/login",
        data={"username": username, "password": password},
    )
    response.raise_for_status()
    token = response.json()["access_token"]

    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    return session


def main() -> None:
    session = make_authorized_session(USERNAME, PASSWORD, BASE_URL)

    agents = session.get(f"{BASE_URL}/api/agents/all").json() # (2)
    print(agents)


if __name__ == "__main__":
    main()
```

1. By default the server includes an admin account with username `admin` and password
`admin`. Change these constants to match your configuration.
2. Use the same `session` object for all subsequent requests — the `Authorization`
header is set once and reused automatically.
