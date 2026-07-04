# Reference Overview

This reference documents the internal API of Consortium. It is generated directly from
the source code and its docstrings, so it always reflects the current state of the
codebase. It is split into three sections, each covering a different layer of the
system.

## Framework

The [Framework](framework/agents-reference.md) section documents the framework
primitives located at `consortium/framework`. These are the base classes, options, and
types that user created components (listeners, agents, plugins, and event hooks) are
built on top of. If you are extending Consortium by writing your own component, this is
the API you compose against. For a guided walkthrough of building components, see the
[Framework](../framework/listeners/listeners-overview.md) manual.

## Services

The [Services](services/agents-service-reference.md) section documents the services
layer located at `consortium/server/services`. Services operate on the framework
primitives and are how the REST API and other parts of the system act on them. Each
service exposes the business logic for a particular area of the framework, such as
listeners, agents, payloads, or user accounts.

## Consortium Exceptions

The [Consortium Exceptions](exceptions/base-consortium-error.md) section documents the
internal exception hierarchy raised by the framework and services, located at
`consortium/server/exceptions/consortium_exceptions`. These exceptions are raised inside
the framework and services and are, at the REST API boundary, wrapped by API exceptions
that attach an HTTP status code. Every exception ultimately derives from a common base
error.
