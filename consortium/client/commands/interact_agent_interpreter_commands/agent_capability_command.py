import re
from argparse import ArgumentParser
from typing import Any

from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import (
    format_object_as_rich_ansi_highlight_str,
    format_rich_text_as_ansi,
    format_value_type_specification_epilog,
    format_value_type_specification_with_examples_epilog,
)
from consortium.client.utils.options_utils import (
    OptionType,
    convert_option_value_strings_to_option_value,
)
from consortium.client.utils.printer_utils import (
    print_error,
    print_info,
)


def _escape_percent_signs(text: str) -> str:
    # Escape percent signs for argparse help text, internally argparse uses
    # percent signs for string formatting. Add a double percent sign to escape.
    return text.replace("%", "%%")


def _construct_help_default_str(value: Any) -> str:
    # Construct a string representation of a default value for help text.
    return (
        format_rich_text_as_ansi("[yellow] (Default: [/]")
        + format_object_as_rich_ansi_highlight_str(value=value)
        + format_rich_text_as_ansi("[yellow])[/]")
    )


def _normalize_option_name(name: str) -> str:
    # Normalize an option name to be compatible with argparse.
    # Converts to lowercase, replaces any non-alphanumeric characters (except
    # underscores) with underscores, and ensures it doesn't start with a digit.
    # Convert to lowercase
    normalized = name.lower()
    # Replace any non-alphanumeric characters (except underscores) with underscores
    normalized = re.sub(r"[^a-z0-9_]", "_", normalized)
    # Collapse multiple underscores into one
    normalized = re.sub(r"_+", "_", normalized)
    # Strip leading/trailing underscores
    normalized = normalized.strip("_")
    # If it starts with a digit, prefix with underscore
    if normalized and normalized[0].isdigit():
        normalized = f"_{normalized}"
    # If empty after normalization, use a placeholder
    if not normalized:
        normalized = "option"
    return normalized


def _generate_abbreviated_flags_from_option_name_list(
    option_name_list: list[str],
    reserved_flags: set[str] | None = None,
) -> dict[str, str]:
    if reserved_flags is None:
        reserved_flags = set()

    flags = {}
    conflicts = []

    # Assign single-letter flags where possible on the first pass.
    for name in option_name_list:
        candidate_flag = f"-{name[0].lower()}"
        if (
            candidate_flag not in flags.values()
            and candidate_flag not in reserved_flags
        ):
            flags[name] = candidate_flag
        else:
            conflicts.append(name)

    # Resolve conflicts on the second pass by finding the next available flag.
    for name in conflicts:
        assigned = False
        for index in range(1, len(name)):
            candidate_flag = f"-{name[: index + 1].lower()}"
            existing_flag_suffixes = [v[1:] for v in flags.values()]
            reserved_flag_suffixes = [v[1:] for v in reserved_flags]
            if (
                name[: index + 1].lower() not in existing_flag_suffixes
                and name[: index + 1].lower() not in reserved_flag_suffixes
            ):
                flags[name] = candidate_flag
                assigned = True
                break
        if not assigned:
            # Fallback: use full name as flag
            flags[name] = f"-{name.lower()}"

    return flags


def _is_single_value_option(option: dict[str, Any]) -> bool:
    # Check if an option accepts a single value
    return option["option_type"] in (
        OptionType.SINGLE_VALUE_OPTION,
        OptionType.CHOICE_VALUE_OPTION,
    )


def _is_multi_value_option(option: dict[str, Any]) -> bool:
    # Check if an option accepts multiple values
    return option["option_type"] in (
        OptionType.LIST_VALUE_OPTION,
        OptionType.TOGGLEABLE_CHOICES_VALUE_OPTION,
        OptionType.DICTIONARY_VALUE_OPTION,
    )


def _determine_positional_options(
    options: dict[str, dict[str, Any]],
) -> list[str]:
    # Returns a list of original option names that should be positional, in order by
    # determining if they accept single or multiple values and if they are required
    # with no default value.
    #
    # Rules:
    # 1. Only arguments that are required AND have no default value can be positional.
    # 2. All required single-value options with NO default value can unconditionally be
    # positional.
    # 3. There can only ever be one required multi-value option with NO default value
    # as a positional, and it must always come last. This option can be bounded or
    # unbounded, and have variable or exact length.

    required_single_value_options: list[str] = []
    required_multi_value_options: list[str] = []

    for original_name, option in options.items():
        if not option["required"] or option["default_value"] is not None:
            continue
        if _is_single_value_option(option):
            required_single_value_options.append(original_name)
        elif _is_multi_value_option(option):
            required_multi_value_options.append(original_name)

    # Multiple required multi-value options, omit all from positional list only return
    # single-value options
    if len(required_multi_value_options) > 1:
        return required_single_value_options

    # Build positional list with single values first, then the single multi-value
    # option last. Due to the earlier checks, there can only be one or no multi-value
    # options here.
    positional_options = required_single_value_options.copy()
    positional_options.extend(required_multi_value_options)

    return positional_options


# Command objects need to be constructed dynamically based on the agent capabilities
# that are present.
def construct_agent_capability_command(
    agent_capability: dict[str, Any],
) -> BaseCommand:
    class AgentCapabilityCommand(BaseCommand):
        name = agent_capability["name"]
        description = agent_capability["description"]
        epilog = format_value_type_specification_epilog()
        group = "Agent Capability Commands"

        # Mapping from original option names to normalized option names
        _original_to_normalized_name_map: dict[str, str] = {}
        # Set of original option names that are positional arguments
        _positional_option_names: set[str] = set()

        def configure_parser(self, parser: ArgumentParser) -> None:
            options = agent_capability["options"]

            # Build the normalized name mapping and handle potential collisions
            normalized_names: dict[str, str] = {}  # normalized -> original
            for original_name in options.keys():
                normalized = _normalize_option_name(original_name)
                # Handle collisions by appending a counter
                base_normalized = normalized
                counter = 1
                while normalized in normalized_names:
                    normalized = f"{base_normalized}_{counter}"
                    counter += 1
                normalized_names[normalized] = original_name

            # Store the mapping: original -> normalized (for use in run())
            self._original_to_normalized_name_map = {
                v: k for k, v in normalized_names.items()
            }

            # Determine which options should be positional
            positional_option_names = _determine_positional_options(options)

            # Store positional option names for use in run()
            self._positional_option_names = set(positional_option_names)

            # Generate abbreviated flags for non-positional options only
            non_positional_normalized_names = [
                norm_name
                for norm_name, orig_name in normalized_names.items()
                if orig_name not in positional_option_names
            ]
            abbreviated_flags = _generate_abbreviated_flags_from_option_name_list(
                non_positional_normalized_names,
                reserved_flags={"-t"},
            )

            # First, add positional arguments in order
            for original_name in positional_option_names:
                normalized_name = self._original_to_normalized_name_map[original_name]
                option = options[original_name]

                # Configure nargs based on option type
                if _is_single_value_option(option):
                    nargs = 1
                else:
                    # Multi-value option (list/toggleable/dictionary)
                    # When a multi-value option is required and has no default value, it
                    # is reasonable to send an empty list or dictionary as the value.
                    # Hence we allow nargs="*" here for 0 or more values. Range
                    # specifications are not supported by argparse so this is as much
                    # as we can reasonably do, we let the server handle more validation.
                    nargs = "*"

                # Determine argparse type
                argparse_type = str
                if _is_single_value_option(option):
                    if option.get("value_type") == "int":
                        argparse_type = int
                    elif option.get("value_type") == "float":
                        argparse_type = float

                # Positionals have no default values
                parser.add_argument(
                    normalized_name,
                    help=_escape_percent_signs(text=option["description"]),
                    nargs=nargs,
                    type=argparse_type,
                    metavar=original_name.upper(),
                )

            # Then, add non-positional arguments as flags
            for normalized_name, original_name in normalized_names.items():
                if original_name in positional_option_names:
                    continue  # Already added as positional

                option = options[original_name]

                # Configure nargs based on option type
                if _is_single_value_option(option):
                    nargs = "?"
                    default = option["default_value"]
                    help_default = (
                        ""
                        if default is None and option["required"]
                        else _construct_help_default_str(value=default)
                    )
                else:
                    nargs = "*"
                    default = None
                    help_default = ""

                # Determine argparse type
                argparse_type = str
                if _is_single_value_option(option):
                    if option.get("value_type") == "int":
                        argparse_type = int
                    elif option.get("value_type") == "float":
                        argparse_type = float

                parser.add_argument(
                    abbreviated_flags[normalized_name],
                    f"--{normalized_name}",
                    help=_escape_percent_signs(text=option["description"])
                    + help_default,
                    nargs=nargs,
                    type=argparse_type,
                    required=option["required"],
                    default=default,
                    metavar=original_name.upper(),
                )

            # Add the value-type flag for explicit type specification
            parser.add_argument(
                "--value-type",
                "-t",
                help="Value type to use for an option value. Applies to all values",
                choices={"str", "int", "float", "bool"},
                nargs="?",
                default=None,
                metavar="VALUE_TYPE",
            )
            parser.add_argument(
                "--help-full",
                help=(
                    "Show this help message and include detailed examples "
                    "for specifying option value types."
                ),
                action="store_true",
            )

        async def run(
            self,
            context: Context,
        ) -> ReturnStatus:
            try:
                # Bypass allowing argparse to parse for the --help-full flag
                # because if a required argument is not provided, argparse
                # will ignore --help-full.
                if "--help-full" in context.arguments:
                    self.parser.epilog = (
                        format_value_type_specification_with_examples_epilog(
                            example_prefix=f"{agent_capability['name']} --<option>"
                        )
                    )
                    self.parser.print_help()
                    self.parser.epilog = self.epilog  # Reset epilog
                    return ReturnStatus(type=ReturnStatusType.CONTINUE)

                parsed_args = self.parser.parse_args(context.arguments)
                client_rest_api_connection = context.client_session.rest_api

                options = agent_capability["options"]
                arguments = {}
                value_type_flag = getattr(parsed_args, "value_type", None)

                for original_name, option in options.items():
                    # Get the normalized name for this option
                    normalized_name = self._original_to_normalized_name_map.get(
                        original_name
                    )
                    if normalized_name is None:
                        continue

                    # Get the value(s) from parsed args using normalized (`parsed_args`
                    # attribute) name
                    option_value = getattr(parsed_args, normalized_name, None)

                    # Skip if no value was provided (None means flag wasn't used)
                    if option_value is None:
                        continue

                    # Handle empty list case
                    if isinstance(option_value, list) and len(option_value) == 0:
                        # For positional multi-value arguments, an empty list is valid
                        # (it means no values were provided, which is allowed for nargs="*")
                        if original_name in self._positional_option_names:
                            # Pass empty list for positional multi-value options
                            arguments[original_name] = []
                            continue
                        else:
                            # For flagged arguments with empty list, use default if available
                            if option.get("default_value") is not None:
                                arguments[original_name] = option["default_value"]
                            continue

                    # For single value options where argparse already converted the type
                    # and no value-type flag was specified, use the value directly
                    if (
                        _is_single_value_option(option)
                        and value_type_flag is None
                        and option.get("value_type") in ("int", "float")
                        and not isinstance(option_value, str)
                        and not isinstance(option_value, list)
                    ):
                        arguments[original_name] = option_value
                        continue

                    # Handle list from positional with nargs=1
                    if isinstance(option_value, list) and len(option_value) == 1:
                        if (
                            _is_single_value_option(option)
                            and value_type_flag is None
                            and option.get("value_type") in ("int", "float")
                            and not isinstance(option_value[0], str)
                        ):
                            arguments[original_name] = option_value[0]
                            continue

                    # Convert to list of strings for options_utils processing
                    if isinstance(option_value, list):
                        value_strings = [str(v) for v in option_value]
                    else:
                        value_strings = [str(option_value)]

                    try:
                        _parameter_name, parameter_value = (
                            convert_option_value_strings_to_option_value(
                                option_json_data=option,
                                value_strings=value_strings,
                                value_type_flag=value_type_flag,
                            )
                        )
                        # Use original name for the arguments dict
                        arguments[original_name] = parameter_value
                    except ValueError as exc:
                        print_error(str(exc))
                        return ReturnStatus(type=ReturnStatusType.CONTINUE)

                _success_response = (
                    await client_rest_api_connection.task_agent_by_agent_id(
                        agent_id=context.interpreter_context["agent"]["agent_id"],
                        command=self.name,
                        arguments=arguments,
                    )
                )
                print_info(
                    f"Tasked agent '{context.interpreter_context['agent']['name']}' "
                    f"({context.interpreter_context['agent']['agent_id']})",
                )
            except SystemExit:
                pass

            return ReturnStatus(
                type=ReturnStatusType.CONTINUE,
            )

    return AgentCapabilityCommand()
