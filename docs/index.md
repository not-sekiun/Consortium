---
hide:
    - navigation
    - toc
    - footer
---

<img alt="Consortium logo" src="assets/logo.png" style="display: block;float: none;margin-left: 45%;margin-right: auto;width: 10%">

<p style="text-align: center;"><i>Consortium: modern C2 framework with a focus on extensibility</i></p>

---

# Consortium

Consortium is a _programming language agnostic_, and _networking protocol agnostic_
command and control (C2) framework that is designed to be _collaborative_,
_highly extensible_, and _modular_. The framework ships with its own listeners and
agents while also allowing users to rapidly develop their own highly customized
listeners and agents.


!!! warning
    Consortium is **actively being developed** and is currently considered to be in the
    _alpha phase_ of development. The current branch `main` is essentially a developer
    branch where I dump all code without regards to correctness. As such it should be
    noted that:

    1. Backwards incompatible/breaking changes may be made to the framework at any time.
    2. The framework may contain major bugs and even incomplete code that can cause crashes.
    3. The framework is currently not considered to be feature-complete.
    4. Documentation will be severely lacking and incomplete.

    I am working to resolve all these and work towards a 1.0.0 release so please raise any
    problems, feature requests, or bug reports in the GitHub issues section.

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

    - Look through the [Server API](rest-api/) to script your own automations and
    write your own clients.
    - Learn how to develop your own [listeners](manual/listeners.md) and
    [agents](manual/agents.md) for the framework to customize it to your needs.
    - Extend the framework even further by developing your own
    [plugins](manual/plugins.md) or [event hooks](manual/event-hooks.md)

-   __Advanced__

    ---

    - Look through the [API reference](reference/) for detailed information on
    the framework components.
    - [Contribute to the core framework code](about/contributing.md) or help
    [improve the documentation](about/contributing.md).

</div>
