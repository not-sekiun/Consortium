# Framework Reference Overview

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
[Framework API](../framework-api/listeners/listeners-overview.md) section.

## Services

The [Services](services/agents-service-reference.md) section documents the services
layer located at `consortium/server/services`. Services operate on the framework
primitives and are how the REST API and other parts of the system act on them. Each
service exposes the business logic for a particular area of the framework, such as
listeners, agents, payloads, or user accounts.

## Exceptions

The [Exceptions](exceptions/exceptions-overview.md) section documents the internal
exception families raised across Consortium: framework exceptions raised by the framework
primitives, object exceptions raised by the server's primitive objects, and service
exceptions raised by the services. The overview explains the common contract every
exception shares (its `code`, `message`, and `detail`), why only the `code` is shown in
these reference pages, and how the three families relate to one another and to the API
exceptions that wrap them at the REST API boundary.
