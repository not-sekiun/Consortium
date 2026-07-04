"""The plugins framework provides the building blocks for defining server plugins.

A plugin is a long-lived background component that runs alongside the server,
implemented by subclassing
[`BasePlugin`][consortium.framework.plugins.BasePlugin]. Plugins are used to integrate
with external services, schedule recurring work, or otherwise augment server behavior,
and are driven through the standard component lifecycle hooks.
"""

from consortium.framework.plugins.base_plugin import BasePlugin

__all__ = ["BasePlugin"]
