"""
Exception hierarchy for listener template framework:

- BaseFrameworkException: Base class for all framework exceptions.
  - ListenerTemplatesFrameworkException: General error occurred in the listener
  templates framework.
    - ListenerTemplateConfigurationError: Error during listener template configuration.
      - ListenerTemplateConfigurationParameterError: Error with a listener template
      parameter.
        - ListenerTemplateConfigurationParameterTypeError: Invalid type for a listener
        template parameter.
        - RequiredListenerTemplateConfigurationParameterNotDeclaredError: Required
        parameter not declared in listener template.
      - EmptyListenerTemplateNameError: Listener template name is an empty string.
      - DuplicateListenerTemplateOptionNameError: Duplicate option name in listener
      template configuration.
    - ListenerTemplateOptionError: Error related to a listener template option.
      - ListenerTemplateOptionNotFoundError: Specified option not found in listener
      template.
      - ListenerTemplateOptionValueError: Invalid value provided for a listener
      template option.
"""

from typing import Any

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ListenerTemplatesFrameworkError(BaseFrameworkException):
    code = "LISTENER_TEMPLATES_FRAMEWORK_ERROR"


class ListenerTemplateConfigurationError(
    comp_excs.ComponentConfigurationError,
    ListenerTemplatesFrameworkError,
):
    """
    Base exception for all errors that occur during the configuration of a particular
    listener template.
    """

    code = "LISTENER_TEMPLATE_CONFIGURATION_ERROR"

    _COMPONENT_TYPE = "listener template"


class InvalidListenerTemplateConfigurationParameterTypeError(
    comp_excs.InvalidComponentConfigurationParameterTypeError,
    ListenerTemplateConfigurationError,
):
    """
    An error that is raised when a listener template's configuration parameter is of an invalid
    type.
    """

    code = "INVALID_LISTENER_TEMPLATE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        listener_template_str: str,
        parameter_name: str,
        parameter_type: str,
    ):
        super().__init__(
            component_str=listener_template_str,
            parameter_name=parameter_name,
            parameter_type=parameter_type,
        )


class MissingListenerTemplateConfigurationParameterError(
    comp_excs.MissingComponentConfigurationParameterError,
    ListenerTemplateConfigurationError,
):
    """
    An error that is raised when a parameter is not declared in a listener template's definition.
    """

    code = "MISSING_LISTENER_TEMPLATE_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, listener_template_str: str, parameter_name: str):
        super().__init__(
            component_str=listener_template_str,
            parameter_name=parameter_name,
        )


class EmptyListenerTemplateLabelError(
    comp_excs.EmptyComponentLabelError,
    ListenerTemplateConfigurationError,
):
    """
    An error that is raised when the label provided in a listener template's definition during
    configuration is an empty string.
    """

    code = "EMPTY_LISTENER_TEMPLATE_LABEL_ERROR"

    def __init__(self, listener_template_filepath: str):
        super().__init__(component_filepath=listener_template_filepath)


class DuplicateListenerTemplateLabelError(
    comp_excs.DuplicateComponentLabelError,
    ListenerTemplateConfigurationError,
):
    """
    An error that is raised when the label provided in the listener template's definition during
    configuration is already in use by another listener template.
    """

    code = "DUPLICATE_LISTENER_TEMPLATE_LABEL_ERROR"

    def __init__(self, listener_template_str: str, label: str):
        super().__init__(
            component_str=listener_template_str,
            label=label,
        )


class InvalidListenerTemplateVersionError(
    comp_excs.InvalidComponentVersionError,
    ListenerTemplateConfigurationError,
):
    """
    An error that is raised when the listener template version string provided in the listener template's
    definition during configuration is not a valid version string according to PEP 440.
    """

    code = "INVALID_LISTENER_TEMPLATE_VERSION_ERROR"

    def __init__(self, listener_template_str: str, version: str):
        super().__init__(
            component_str=listener_template_str,
            version=version,
        )


class InvalidFrameworkVersionSpecifierError(
    comp_excs.InvalidFrameworkVersionSpecifierError,
    ListenerTemplateConfigurationError,
):
    """
    An error that is raised when the framework version specifier string provided in the
    listener template's definition during configuration is not a valid version specifier string as
    defined in PEP440.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"

    def __init__(
        self,
        listener_template_str: str,
        framework_version_specifier_str: str,
    ):
        super().__init__(
            component_str=listener_template_str,
            framework_version_specifier_str=framework_version_specifier_str,
        )


class InvalidListenerTemplateDependencyVersionSpecifierError(
    comp_excs.InvalidComponentDependencyVersionSpecifierError,
    ListenerTemplateConfigurationError,
):
    """
    An error that is raised when the listener template dependency version specifier string
    provided in the listener template's definition during configuration is not a valid version
    specifier string as defined in PEP440.
    """

    code = "INVALID_LISTENER_TEMPLATE_DEPENDENCY_VERSION_SPECIFIER_ERROR"

    def __init__(
        self,
        listener_template_str: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_str=listener_template_str,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class DuplicateListenerTemplateOptionNameError(ListenerTemplateConfigurationError):
    code = "DUPLICATE_LISTENER_TEMPLATE_OPTION_NAME_ERROR"

    def __init__(self, listener_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to configure the listener template {listener_template_str}'. "
                f"The options provided to the listener template must not have "
                f"duplicate names but the name '{option_name}' was duplicated."
            ),
        )


# class ListenerTemplateConfigurationParameterError(ListenerTemplateConfigurationError):
#     pass

# class MissingListenerTemplateConfigurationParameterError(
#     ListenerTemplateConfigurationParameterError,
# ):
#     def __init__(self, listener_template_str: str, parameter_name: str):
#         super().__init__(
#             message=(
#                 f"Failed to configure the listener template "
#                 f"'{listener_template_str}'. The required parameter "
#                 f"'{parameter_name}' was not declared in the listener template's "
#                 f"definition."
#             ),
#         )

# class ListenerTemplateConfigurationError(ListenerTemplatesFrameworkError):
#     pass
#
#

#
#
# class ListenerTemplateConfigurationParameterTypeError(
#     ListenerTemplateConfigurationParameterError,
# ):
#     def __init__(
#         self,
#         listener_template_str: str | None = None,
#         parameter_name: str | None = None,
#         parameter_type: str | None = None,
#         error_message: str = "",
#     ):
#         if not error_message:
#             super().__init__(
#                 message=(
#                     f"Failed to configure the listener template "
#                     f"'{listener_template_str}'. The parameter '{parameter_name}' "
#                     f"must be of type '{parameter_type}' in the listener template's "
#                     f"definition."
#                 ),
#             )
#         else:
#             super().__init__(
#                 message=(
#                     f"Failed to configure the listener template "
#                     f"'{listener_template_str}'. {error_message}"
#                 ),
#             )
#
#

#
#
# class EmptyListenerTemplateNameError(ListenerTemplateConfigurationError):
#     def __init__(self, listener_template_filepath: str):
#         super().__init__(
#             message=(
#                 f"Failed to configure the listener template defined at "
#                 f"'{listener_template_filepath}'. The name provided in the listener "
#                 f"template's definition during configuration cannot be empty."
#             ),
#         )
#
#


class ListenerTemplateOptionError(ListenerTemplatesFrameworkError):
    code = "LISTENER_TEMPLATE_OPTION_ERROR"


class ListenerTemplateOptionNotFoundError(ListenerTemplateOptionError):
    code = "LISTENER_TEMPLATE_OPTION_NOT_FOUND_ERROR"

    def __init__(self, listener_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to access the option '{option_name}' for the listener "
                f"template {listener_template_str}. Could not find the requested "
                f"option '{option_name}' in the agent template."
            ),
            detail={"option_name": option_name},
        )


class ListenerTemplateOptionValueError(ListenerTemplateOptionError):
    code = "LISTENER_TEMPLATE_OPTION_VALUE_ERROR"

    def __init__(
        self,
        listener_template_str: str,
        option_name: str,
        option_value: Any,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to set the option '{option_name}' to the value "
                f"'{option_value}' for the listener template "
                f"'{listener_template_str}'. {error_message}"
            ),
            detail={
                "option_name": option_name,
                "option_value": option_value,
                "message": error_message,
            },
        )
