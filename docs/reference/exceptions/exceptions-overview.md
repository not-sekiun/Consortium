# Exceptions Overview

Consortium raises typed exceptions internally rather than returning error codes or ad hoc
strings. These exceptions are split into three families, the "trinity", each rooted at its
own common base error:

- **Framework exceptions** ([`BaseFrameworkError`][consortium.framework._core.framework_exceptions.base_framework_exception.BaseFrameworkError]),
  located at `consortium/framework/_core/framework_exceptions`. Raised by the framework
  primitives (agents, listeners, plugins, event hooks, agent generators, and their
  supporting types) as they are configured, created, and operated on.
- **Object exceptions** ([`BaseObjectError`][consortium.server.exceptions.object_exceptions.base_object_exception.BaseObjectError]),
  located at `consortium/server/exceptions/object_exceptions`. Raised by the server's
  primitive objects (such as agents and repository resources) that live in the server but
  are not framework primitives.
- **Service exceptions** ([`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]),
  located at `consortium/server/exceptions/service_exceptions`. Raised by the services
  that orchestrate the framework primitives and objects on behalf of the REST API.

## The shared contract: `code`, `message`, `detail`

Every exception in all three families, whichever base it derives from, carries the same
three public attributes:

- **`code`**: a stable, machine-readable string in `SCREAMING_SNAKE_CASE` that uniquely
  identifies the kind of error (for example `AGENT_NOT_FOUND_ERROR`). It is declared as a
  class attribute and is the one part of an exception that callers can rely on without
  depending on the concrete exception class.
- **`message`**: a human-readable description of what went wrong and, where possible, how
  to resolve it. It is populated per instance when the exception is raised.
- **`detail`**: optional structured, machine-readable context about the error (for example
  the offending identifier), or `None` when there is no such context. It is also populated
  per instance.

## Why only `code` is shown in these pages

The reference pages below are generated directly from the exception classes. Because
`message` and `detail` are instance attributes that are only populated when an exception
is actually raised (inside each exception's `__init__`), they have no meaningful value at
the class level and would render as empty fields. To keep the documentation focused, each
page filters `message` and `detail` out, so only the stable `code` is shown for each
exception. The `code` is therefore the canonical, documented identifier for every error;
the accompanying `message` and `detail` are constructed at raise time.

## How the families relate to each other

Within a family, every exception ultimately derives from that family's base error, so an
entire family can be caught through a single common type. The three bases are independent
roots; they are related by role rather than by inheritance:

- Services sit at the top of the call stack and may surface their own service exceptions
  or propagate framework and object exceptions raised beneath them.
- At the REST API boundary, any of the three is wrapped by a matching API exception. The
  wrapper copies the internal exception's `message`, `detail`, and `code`, and attaches an
  HTTP status code, so `code` is what links an internal error to the response a client
  ultimately sees.

For the individual errors in each family, see the Framework Exceptions, Object Exceptions,
and Service Exceptions sections.
