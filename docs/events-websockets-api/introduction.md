The events websockets API is how you can subscribe to events that occur in the
framework and receive updates in real-time. The websocket endpoint is located at
`/api/events` on the REST API server. Unlike the rest of the REST API endpoints which
are automatically documented under the [OpenAPI](https://www.openapis.org/) initiative,
the events API runs over a websocket which is not supported by OpenAPI. Hence, this is
the only place where you will find information on how to use the API.

## Overview
At a high level, the process of using the events API looks like this.

1. The client authenticates itself to the framework's server by making a POST request
to the authentication endpoint at `/api/login` (Similarly to how a client would
typically login). The client will receive a [JSON Web Token](https://jwt.io/) that will
be used to prove its identity to the server.
2. The client then makes a websocket connection to `/api/events` with its provided JSON
Web Token included as part of its `Authorization` header to not be rejected with a `401
Unauthorized` response from the server.
3. The client sends action commands (formatted as JSON strings) over the websocket to
the server to perform things like subscribing, unsubscribing, or viewing subscribed
events, etc.
4. The client can then listen for responses from the websocket that are pushed to it
whenever a subscribed event occurs. Data from that event is sent to the client (again,
formatted as JSON strings)

## Usage
The events API is designed to be used in two ways.

1. As a component of a custom written client. Oftentimes it is necessary for clients to
respond to server initiated push events so that they can alert their user in real time
without requiring a polling request (e.g. updating when an agent calls back for the
first time).
2. The more common usage, as a standalone application. Users might want
scripting/automation capabilities that allow them to respond in real time to events
that occur on the server.

For simplicity's sake this documentation will focus on the second use case. We will
build from the ground up a simple notification system to demonstrate how to use the
events API.
