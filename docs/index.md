---
hide:
    - navigation
    - toc
    - footer
---

![Consortium Logo](assets/banner_light_mode.png#only-light){ width="75%" }
![Consortium Logo](assets/banner_dark_mode.png#only-dark){ width="75%" }
{ style="text-align: center;" }

<p style="text-align: center;"><i>A modern C2 framework with a focus on extensibility</i></p>

---

Consortium is a _programming language agnostic_, and _networking protocol agnostic_
command and control (C2) framework that is designed to be _collaborative_,
_highly extensible_, and _modular_. The framework ships with its own listeners and
agents while also allowing users to rapidly develop their own highly customized
listeners and agents.

!!! warning
    Consortium is **actively being developed** and is currently considered to be in the
    _alpha phase_ of development. As such it should be noted that:

    1. Backwards incompatible/breaking changes may be made at any time.
    2. The framework is currently not considered to be feature-complete.
    3. Documentation will be lacking and incomplete.

    Feel free to raise any problems, feature requests, or bug reports in the GitHub
    issues section.

<div class="grid cards" markdown>

-   __Getting Started__

    ---

    - [Install Consortium](getting-started/installation.md) and get the framework
    [up and running](getting-started/quick-start.md) as quickly as possible.
    - Learn about the [basic concepts](about/) and [features](about/features.md)
    that are unique to the framework.
    - Explore the [high level usage](manual/) of the framework.

-   __Usage__

    ---

    - Look through the [Server REST API](server-api/rest-api) or
    [Server Events Websockets API](server-api/events-websockets-api) to script
    automations and write custom clients.
    - Develop custom [listeners](framework/listeners/listeners-overview.md) and
    [agents](framework/agents/agents-overview.md) for the framework.
    - Extend the framework further through writing
    [plugins](framework/plugins/plugins-overview.md) or [event hooks](framework/event-hooks/event-hooks-overview.md)

-   __Advanced__

    ---

    - Look through the [API reference](reference/) for detailed information on
    the framework components.
    - [Contribute to the core framework code](about/contributing.md) or help
    [improve the documentation](about/contributing.md).

</div>
