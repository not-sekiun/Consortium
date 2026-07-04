The events websockets API lets you subscribe to events that occur in the framework and
receive real-time push notifications. The endpoint is at `/api/events`. Unlike the REST
API, websockets are not covered by [OpenAPI](https://www.openapis.org/). This page is
the only reference for
the events API.

## Overview

1. `POST /api/login` with credentials to receive a [JSON Web Token](https://jwt.io/).
2. Open a websocket to `/api/events` with the token in the `Authorization` header.
3. Send action commands as JSON strings to subscribe, unsubscribe, or query
   subscriptions.
4. Receive event payloads as JSON whenever a subscribed event fires.

## Usage

The events API suits two use cases: embedding in a client to react to server-push events
without polling, or running standalone for scripting and automation. This documentation
focuses on the standalone case, building a simple notification system from the ground
up.
