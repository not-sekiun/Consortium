"""Helper utilities for use within agent generator build steps.

These are small, general-purpose helpers that build steps commonly reach for when
producing an agent payload, such as
[`run_command`][consortium.framework.agents.agent_generator_utils.run_command] for
invoking external build tooling in a subprocess and
[`multiple_string_replace`][consortium.framework.agents.agent_generator_utils.multiple_string_replace]
for templating source files before compilation.
"""

from consortium.framework.agents.agent_generator_utils.shell_utils import run_command
from consortium.framework.agents.agent_generator_utils.string_utils import (
    multiple_string_replace,
)

__all__ = [
    "run_command",
    "multiple_string_replace",
]
