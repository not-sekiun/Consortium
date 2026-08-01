# User Accounts

By default, the server loads user account information from `data/server/user_accounts.json`.
This file describes the credentials of every user account allowed to connect to the server
over its REST API and Events WebSockets API, along with the role assigned to each account.

!!! warning
    It is **highly recommended** to change the default user accounts before deploying the
    server to prevent unauthorized access.

These are the default user accounts that are present.

```json title="user_accounts.json"
[
    {
        "username": "admin",
        "password": "admin",
        "role": "ADMIN"
    },
    {
        "username": "operator",
        "password": "operator",
        "role": "OPERATOR"
    },
    {
        "username": "spectator",
        "password": "spectator",
        "role": "SPECTATOR"
    }
]
```

| Field      | Description                                           | Restrictions                                                                                                                                                                            |
|------------|-------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `username` | The username of the user.                             | - Cannot contain leading or trailing whitespace characters.<br>- Cannot be an empty string.<br>- Can only contain printable ASCII characters.<br>- Must be unique across user accounts. |
| `password` | The password of the user.                             | - Cannot be an empty string.<br>- Can only contain printable ASCII characters.                                                                                                          |
| `role`     | The role controlling the user's access to the server. | - Must correspond to a role defined in [`role_permissions.json`](roles-and-permissions.md).                                                                                             |

The `role` field determines the permissions a user has when connecting to the server. The
three roles shipped by default provide the following broad levels of access:

| Role        | Permissions                                                                                                   |
|-------------|---------------------------------------------------------------------------------------------------------------|
| `ADMIN`     | Can perform all actions on the server.                                                                        |
| `OPERATOR`  | Can perform most actions on the server except actions that **involve managing other user accounts or users**. |
| `SPECTATOR` | Can only perform actions that **read** information from the server.                                           |

The exact permissions granted by each role, and how to customize roles or define your own,
are covered in [Roles and Permissions](roles-and-permissions.md).
