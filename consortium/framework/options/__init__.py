"""
The options framework provides a set of options classes, [`SingleValueOption`][consortium.framework.options.SingleValueOption],
[`ListValueOption`][consortium.framework.options.ListValueOption], [`ChoiceValueOption`][consortium.framework.options.ChoiceValueOption],
[`ToggleableChoicesValueOption`][consortium.framework.options.ToggleableChoicesValueOption],
and [`DictionaryValueOption`][consortium.framework.options.DictionaryValueOption] that
are used across the framework to define the parameters that different framework
components accept as well as to perform validation on the arguments that are set on
those options.

The options classes should be imported and used from this module.

Example:
    ```python
    from consortium.framework.options import (
        SingleValueOption,
        ListValueOption,
        ChoiceValueOption,
        ToggleableChoicesValueOption,
        DictionaryValueOption,
    )
    ```

The `__all__` variable is set to only include the options classes along with the
[`OptionType`][consortium.framework.options.option_types.OptionType] enum so you can
(but are not recommended to) import all the options classes at once using the following
import statement:

Example:
    ```python
    from consortium.framework.options import *
    ```
"""

from consortium.framework.options.choice_value_option import ChoiceValueOption
from consortium.framework.options.dictionary_value_option import DictionaryValueOption
from consortium.framework.options.list_value_option import ListValueOption
from consortium.framework.options.option_types import OptionType
from consortium.framework.options.single_value_option import SingleValueOption
from consortium.framework.options.toggleable_choices_value_option import (
    ToggleableChoicesValueOption,
)

__all__ = [
    "OptionType",
    "SingleValueOption",
    "ListValueOption",
    "ChoiceValueOption",
    "ToggleableChoicesValueOption",
    "DictionaryValueOption",
]
