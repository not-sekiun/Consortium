---
hide:
    - navigation
    - toc
    - footer
---

# Home

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
    - Explore the high level usage of the framework through the
      [Consortium client](client/client-overview.md).

-   __Usage__

    ---

    - Look through the [Server REST API](server-api/rest-api/introduction.md) or
      [Server Events Websockets API](server-api/events-websockets-api/introduction.md)
      to script automations and write custom clients.
    - Develop custom [listeners](framework/listeners/listeners-overview.md) and
      [agents](framework/agents/agents-overview.md) for the framework.

-   __Advanced__

    ---

    - Extend the framework further through writing
      [plugins](framework/plugins/plugins-overview.md)
      or [event hooks](framework/event-hooks/event-hooks-overview.md)
    - Look through the [API reference](reference/reference-overview.md) for more
      information on working with framework components.

</div>
