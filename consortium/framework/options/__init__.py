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

Additionally, the options framework provides a set of validating functions that can be
used to validate option values.

Example:
    ```python
    from consortium.framework.options import validate_is_ip_address
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
from consortium.framework.options.validating_functions import (
    validate_is_cidr,
    validate_is_datetime,
    validate_is_directory_and_exists,
    validate_is_file_and_exists,
    validate_is_filesystem_path_and_exists,
    validate_is_http_url,
    validate_is_ip_address,
    validate_is_url,
    validate_is_url_path,
    validate_is_uuid4,
)

__all__ = [
    "OptionType",
    "SingleValueOption",
    "ListValueOption",
    "ChoiceValueOption",
    "ToggleableChoicesValueOption",
    "DictionaryValueOption",
    "validate_is_url_path",
    "validate_is_filesystem_path_and_exists",
    "validate_is_url",
    "validate_is_cidr",
    "validate_is_datetime",
    "validate_is_uuid4",
    "validate_is_http_url",
    "validate_is_ip_address",
    "validate_is_directory_and_exists",
    "validate_is_file_and_exists",
]
