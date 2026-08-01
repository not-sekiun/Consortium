# Agent Protocol

This document describes what an agent binary must implement to communicate with a
Consortium listener. The framework defines the server-side protocol obligations (via
`ConnectedAgentsService`), but the wire protocol is defined by the listener
implementation. The protocol described here matches the built-in HTTP listener in
`consortium/components/listeners/consortium/http/`.

If you are writing an agent for a custom listener, replace the HTTP-specific details
with whatever transport your listener implements. The three obligations remain the same
regardless of transport: register, poll for tasks, and submit results.

---

## The three-message loop

An agent's runtime loop has three phases that repeat for its entire lifetime:

```
1. Registration (once, on first connection)
   Agent -> Listener: identity information
   Listener -> Agent: assigned agent_id

2. Check-in / task poll (repeated at a configured interval)
   Agent -> Listener: agent_id
   Listener -> Agent: list of pending TaskLaunchMessageModel objects

3. Result submission (once per completed task)
   Agent -> Listener: agent_id + task_id + output
   Listener -> Agent: acknowledgement
```

---

## 1. Registration

The agent must register before the framework will accept check-ins from it. Registration
associates the agent with a listener and creates its record in the framework.

### HTTP listener

**Request**

```
POST /register   (URL path is configurable via the listener's registration_url_paths option)
Content-Type: application/json

{
    "payload_id":          "<uuid>",      # preferred: ID of the generated payload
    "agent_type":          "<string>",    # fallback: agent type name (e.g. "recon_agent")
    "user":                "<string>",    # OS username running the agent
    "is_admin":            <bool>,        # elevated privileges
    "os":                  "<string>",    # operating system string
    "version":             "<string>",    # OS version
    "arch":                "<string>",    # CPU architecture (e.g. "x86_64")
    "pid":                 <int>,         # process ID
    "locale":              "<string>",    # system locale (e.g. "en-US")
    "local_ip":  "<string>",   # agent's local IP
    "hostname":            "<string>"    # agent's hostname
}
```

Exactly one of `payload_id` or `agent_type` must be present. Using `payload_id` is
strongly preferred: it links the agent back to the generated payload and allows the
framework to resolve the agent type automatically. All other fields are optional but
improve the agent's detail view.

**Response (200 OK)**

```json
{
    "agent_id": "<uuid>"
}
```

The agent must store the returned `agent_id`. It is the agent's identity for all
subsequent requests.

**Response on failure (401 Unauthorized)**

The agent should disconnect and optionally retry after a delay.

---

## 2. Check-in and task retrieval

The agent polls the listener at a configurable interval to receive pending tasks. The
check-in is also how the framework records that the agent is alive (it updates
`datetime_last_checked_in`).

### HTTP listener

**Request**

```
GET /tasks   (URL path is configurable via tasks_url_paths)
Cookie: <agent_id>
```

The `Cookie` header carries the `agent_id` returned during registration.

**Response (200 OK)**

```json
[
    {
        "task_id":   "<uuid>",
        "command":   "<capability name>",
        "arguments": { "<option_name>": <value>, ... },
        "data":      {}
    },
    ...
]
```

An empty array `[]` means no tasks are pending. The agent should sleep for its
configured delay and poll again.

Each task object in the array is a `TaskLaunchMessageModel` serialized via
`to_json()`. The agent executes each task independently:

`to_json()` is the server-side serialization method. Agent implementations should depend
on the JSON object shape shown above, rather than on that Python method name.

- `command`: the capability name to execute (e.g. `"shell"`, `"info"`, `"download"`)
- `arguments`: the validated option values provided by the operator
- `data`: additional structured data; may be empty
- `task_id`: must be echoed back in all result messages for this task

Binary payloads (`payload`) are excluded from `to_json()`. If a listener transmits
binary payloads it does so via an additional channel (multipart, base64 encoding, etc.).

**Response on failure (401 Unauthorized)**

The agent should treat this as a de-registration signal and either reconnect (
re-register)
or exit, depending on its configuration.

---

## 3. Result submission

After executing a task (or when a task fails), the agent submits a result. The result
must include the `task_id` returned in the original task message.

### HTTP listener (JSON-only result)

**Request**

```
POST /results   (URL path is configurable via results_url_paths)
Content-Type: application/json
Cookie: <agent_id>

{
    "task_id": "<uuid>",
    "success": <bool>,
    "message": "<string>",
    "data":    { ... }
}
```

- `task_id`: matches the task being completed
- `success`: `true` if the task succeeded, `false` otherwise
- `message`: human-readable output or error description
- `data`: structured output; may be empty `{}`

**Response (200 OK)**

The listener responds with status 200 and an empty body. The agent can discard the
response body.

### HTTP listener (binary payload result)

When a task produces binary output (file download, screenshot, etc.), the agent uses
multipart form data:

**Request**

```
POST /results
Content-Type: multipart/form-data; boundary=<boundary>
Cookie: <agent_id>

--<boundary>
Content-Disposition: form-data; name="json"
Content-Type: application/json

{"task_id": "<uuid>", "success": true, "message": "...", "data": {}}

--<boundary>
Content-Disposition: form-data; name="payload"
Content-Type: application/octet-stream

<binary data>
--<boundary>--
```

The `json` part carries the result metadata. The `payload` part carries the raw binary.

---

## Multi-message tasks

Some capabilities require more than one round trip. A file download capability, for
example, expects the agent to send a series of messages after the initial task is
dispatched:

```
Server (sends)  -> Agent: TaskLaunchMessageModel  {command: "download", arguments: {source: "/etc/passwd"}}
Agent  (sends)  -> Server: {success: true, data: {type: "file", path: "/etc/passwd", size: 1024}}
Agent  (sends)  -> Server: {success: true, data: {type: "chunk"}, payload: <binary chunk>}
Agent  (sends)  -> Server: {success: true, data: {type: "end_of_transfer"}}
```

The capability's `on_execute()` method calls `await self.recv_from_agent()` once per
expected message. Each call blocks until the agent submits a result message with the
matching `task_id`. The agent must therefore submit multiple result messages for the
same `task_id` until the exchange is complete.

The wire format for each additional message is the same as a normal result submission.

---

## Protocol implementation checklist

When implementing an agent for a custom listener, ensure the agent:

- [ ] Sends a registration message on startup and stores the returned `agent_id`
- [ ] Re-registers if the server responds with 401 Unauthorized to a check-in
- [ ] Polls for tasks at a configurable interval (with optional jitter)
- [ ] Executes each received task concurrently or sequentially (depending on the
  capability)
- [ ] Submits a result for every task received, even on failure
- [ ] Echoes back the `task_id` from the task message in every result message
- [ ] Handles multi-message exchanges by submitting multiple results with the same
  `task_id` until the server capability signals completion
- [ ] Disconnects gracefully when the listener stops sending responses

---

## Complete HTTP agent loop (pseudocode)

```python
# Registration
response = post("/register", {
  "payload_id": PAYLOAD_ID,
  "user": os.getlogin(),
  "is_admin": is_admin(),
  "os": platform.system(),
  "hostname": socket.gethostname(),
  ...
})
agent_id = response["agent_id"]

# Main loop
while True:
  # Poll for tasks
  tasks = get("/tasks", headers={"Cookie": agent_id})
  for task in tasks:
    result = execute(task["command"], task["arguments"])
    post("/results", {
      "task_id": task["task_id"],
      "success": result.success,
      "message": result.message,
      "data": result.data,
    }, headers={"Cookie": agent_id})

  sleep(SLEEP_TIME + random_jitter(SLEEP_TIME_JITTER))
```
