# Server Overview

The server exposes its functionality to clients through two complementary interfaces: a
request/response REST API and a push-based events websockets API. Together they let you
drive the framework and react to what happens inside it.

## REST API

The [REST API](rest-api/introduction.md) is the primary way to interact with the server.
It is a thin request/response layer over the framework's services, covering operations
such as authenticating, managing listeners and agents, building payloads, and working
with assets and artifacts. It is automatically documented via OpenAPI (Swagger UI and
ReDoc), and most endpoints require a Bearer token obtained from `/api/login`.

See the [REST API introduction](rest-api/introduction.md) for the base URL, interactive
documentation, and authentication.

## Events Websockets API

The [Events Websockets API](events-websockets-api/introduction.md) provides real-time,
server-push notifications. Instead of polling the REST API, you open a websocket to
`/api/events`, subscribe to the events you care about, and receive their payloads as JSON
the moment they fire. This suits both clients reacting to server activity and standalone
scripts for automation.

See the [Events Websockets API introduction](events-websockets-api/introduction.md) to
get started with subscriptions and action commands.
