# Roles and Permissions

Access to the server is governed by **roles**. Every user account is assigned a role (see
[User Accounts](user-accounts.md)), and each role grants a set of fine grained
**permissions**, where every permission authorizes a single action against the server's
REST API or Events WebSockets API.

By default, the server loads its roles from `data/server/role_permissions.json`. This file
maps each role name to the list of permissions that role grants.

```json title="role_permissions.json"
{
    "ADMIN": [
        "CREATE_USER_ACCOUNT",
        "READ_ALL_USER_ACCOUNTS",
        "CREATE_LISTENER",
        "..."
    ],
    "OPERATOR": [
        "READ_OWN_USER_ACCOUNT",
        "CREATE_LISTENER",
        "..."
    ],
    "SPECTATOR": [
        "READ_ALL_LISTENERS",
        "READ_ALL_AGENTS",
        "..."
    ]
}
```

## Customizing roles

You can tailor the permissions of the built in roles, or define entirely new roles, by
editing `role_permissions.json`:

- **Add or remove a permission** by editing the permission list for a role.
- **Create a new role** by adding a new top level key whose value is the list of
  permissions it grants. Any account assigned that role name in
  [`user_accounts.json`](user-accounts.md) then receives those permissions.
- **Remove a role** by deleting its key. Make sure no user account still references a role
  before removing it.

!!! warning
    Every entry in a role's permission list must be a valid permission string. Unknown
    permission strings are rejected when the file is loaded and the server will fail to
    start. The valid permission strings are listed in the [permission
    catalog](#permission-catalog) below.

## Permission catalog

The permissions below are the complete set the server recognizes. They are grouped by the
REST API endpoint (or Events WebSockets API) they authorize.

### User account and session management

| Permission                               | Grants                                              |
|------------------------------------------|-----------------------------------------------------|
| `LOGOUT_USER_ACCOUNT_BY_USER_ACCOUNT_ID` | Log out a user account by its user account ID.      |
| `LOGOUT_USER_BY_USER_ID`                 | Log out a user by its user ID.                      |
| `CREATE_USER_ACCOUNT`                    | Create a new user account.                          |
| `READ_USER_ACCOUNT_BY_USER_ACCOUNT_ID`   | Read a user account by its user account ID.         |
| `READ_ALL_USER_ACCOUNTS`                 | Read all user accounts.                             |
| `READ_OWN_USER_ACCOUNT`                  | Read the caller's own user account.                 |
| `UPDATE_OWN_USER_ACCOUNT`                | Update the caller's own user account.               |
| `UPDATE_USER_ACCOUNT_BY_USER_ACCOUNT_ID` | Update any user account by its user account ID.     |
| `DELETE_USER_ACCOUNT_BY_USER_ACCOUNT_ID` | Delete a user account by its user account ID.       |

### Users

| Permission               | Grants                                  |
|--------------------------|-----------------------------------------|
| `READ_OWN_USER`          | Read the caller's own user.             |
| `READ_ALL_USERS`         | Read all connected users.               |
| `READ_USER_BY_USER_ID`   | Read a user by its user ID.             |
| `UPDATE_OWN_USER`        | Update the caller's own user.           |
| `UPDATE_USER_BY_USER_ID` | Update a user by its user ID.           |

### Server

| Permission            | Grants                             |
|-----------------------|------------------------------------|
| `READ_SERVER_RELEASE` | Read the server's release version. |
| `READ_SERVER_CONFIG`  | Read the server's configuration.   |

### Listeners

| Permission                                       | Grants                                             |
|--------------------------------------------------|----------------------------------------------------|
| `CREATE_LISTENER`                                | Create a listener from a listener template.        |
| `READ_ALL_LISTENER_TEMPLATES`                    | Read all listener templates.                       |
| `READ_LISTENER_TEMPLATE_BY_LISTENER_TEMPLATE_ID` | Read a listener template by its ID.                |
| `READ_ALL_LISTENERS`                             | Read all listeners.                                |
| `READ_LISTENER_BY_LISTENER_ID`                   | Read a listener by its listener ID.                |
| `START_LISTENER_BY_LISTENER_ID`                  | Start a listener by its listener ID.               |
| `STOP_LISTENER_BY_LISTENER_ID`                   | Stop a listener by its listener ID.                |
| `CANCEL_LISTENER_BY_LISTENER_ID`                 | Cancel a listener by its listener ID.              |
| `UPDATE_LISTENER_BY_LISTENER_ID`                 | Update a listener by its listener ID.              |
| `DELETE_LISTENER_BY_LISTENER_ID`                 | Delete a listener by its listener ID.              |

### Agent generators and agents

| Permission                                     | Grants                                               |
|------------------------------------------------|------------------------------------------------------|
| `CREATE_AGENT_GENERATOR`                       | Create an agent generator from an agent template.    |
| `READ_ALL_AGENT_TEMPLATES`                     | Read all agent templates.                            |
| `READ_AGENT_TEMPLATE_BY_AGENT_TEMPLATE_ID`     | Read an agent template by its ID.                    |
| `READ_ALL_AGENT_GENERATORS`                    | Read all agent generators.                           |
| `READ_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID`   | Read an agent generator by its ID.                   |
| `START_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID`  | Start an agent generator by its ID.                  |
| `STOP_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID`   | Stop an agent generator by its ID.                   |
| `CANCEL_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID` | Cancel an agent generator by its ID.                 |
| `UPDATE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID` | Update an agent generator by its ID.                 |
| `DELETE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID` | Delete an agent generator by its ID.                 |
| `READ_ALL_AGENTS`                              | Read all agents.                                     |
| `READ_AGENT_BY_AGENT_ID`                       | Read an agent by its agent ID.                       |
| `READ_ALL_AGENT_TASKS`                         | Read all agent tasks.                                |
| `READ_ALL_AGENT_TASKS_BY_AGENT_ID`             | Read all tasks for a given agent.                    |
| `READ_AGENT_TASK_BY_AGENT_ID_AND_TASK_ID`      | Read a specific task for a given agent.              |
| `READ_AGENT_TASK_BY_TASK_ID`                   | Read an agent task by its task ID.                   |
| `TASK_AGENT_BY_AGENT_ID`                       | Task an agent by its agent ID.                       |
| `UPDATE_AGENT_BY_AGENT_ID`                     | Update an agent by its agent ID.                     |
| `DELETE_AGENT_BY_AGENT_ID`                     | Delete an agent by its agent ID.                     |
| `DELETE_AGENT_TASK_BY_TASK_ID`                 | Delete an agent task by its task ID.                 |

### Events WebSockets API

| Permission             | Grants                                          |
|------------------------|-------------------------------------------------|
| `USE_EVENTS_WEBSOCKET` | Connect to and use the Events WebSockets API.   |

### Assets

| Permission                 | Grants                            |
|----------------------------|-----------------------------------|
| `UPLOAD_ASSETS`            | Upload assets to the server.      |
| `DOWNLOAD_ASSETS`          | Download assets from the server.  |
| `READ_ALL_ASSETS`          | Read all assets.                  |
| `READ_ASSET_BY_ASSET_ID`   | Read an asset by its asset ID.    |
| `UPDATE_ASSET_BY_ASSET_ID` | Update an asset by its asset ID.  |
| `DELETE_ASSET_BY_ASSET_ID` | Delete an asset by its asset ID.  |

### Artifacts

| Permission                       | Grants                                 |
|----------------------------------|----------------------------------------|
| `DOWNLOAD_ARTIFACTS`             | Download artifacts from the server.    |
| `READ_ALL_ARTIFACTS`             | Read all artifacts.                    |
| `READ_ARTIFACT_BY_ARTIFACT_ID`   | Read an artifact by its artifact ID.   |
| `UPDATE_ARTIFACT_BY_ARTIFACT_ID` | Update an artifact by its artifact ID. |
| `DELETE_ARTIFACT_BY_ARTIFACT_ID` | Delete an artifact by its artifact ID. |

### Payloads

| Permission                     | Grants                               |
|--------------------------------|--------------------------------------|
| `DOWNLOAD_PAYLOADS`            | Download payloads from the server.   |
| `READ_ALL_PAYLOADS`            | Read all payloads.                   |
| `READ_PAYLOAD_BY_PAYLOAD_ID`   | Read a payload by its payload ID.    |
| `UPDATE_PAYLOAD_BY_PAYLOAD_ID` | Update a payload by its payload ID.  |
| `DELETE_PAYLOAD_BY_PAYLOAD_ID` | Delete a payload by its payload ID.  |
