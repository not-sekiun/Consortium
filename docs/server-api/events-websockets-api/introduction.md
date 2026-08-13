The events websockets API lets you subscribe to events that occur in the framework and
receive real-time push notifications. The endpoint is at `/api/ws/events`. Unlike the
REST API, websockets are not covered by [OpenAPI](https://www.openapis.org/). This page
is the only reference for the events API.

## Overview

1. `POST /api/login` with credentials to receive a [JSON Web Token](https://jwt.io/).
2. `POST /api/ws/ticket` with that token in the `Authorization` header to receive a
   short-lived, single-use ticket. A websocket handshake cannot carry a header, so the
   token is exchanged for a credential that can travel in the URL.
3. Open a websocket to `/api/ws/events?ticket=TICKET`.
4. Send action commands as JSON strings to subscribe, unsubscribe, or query
   subscriptions.
5. Receive event payloads as JSON whenever a subscribed event fires.

Each connection needs its own freshly issued ticket. See
[authentication](authentication.md) for the full exchange.

## Usage

The events API suits two use cases: embedding in a client to react to server-push events
without polling, or running standalone for scripting and automation. This documentation
focuses on the standalone case, building a simple notification system from the ground
up.
