"""A collection of ready-made validating functions for option values.

Each function follows the validating function contract expected by the options
framework: it takes the option's value as its single argument and returns None if the
value is valid, or raises
[`OptionValueValidationError`][consortium.framework.exceptions.options_framework_exceptions.OptionValueValidationError]
if it is not. Pass one of these to the `validating_function` parameter of an option to
enforce the corresponding constraint, for example requiring that a value be a valid IP
address or an existing filesystem path.
"""

import ipaddress
import pathlib
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse

from consortium.framework.signal_exceptions.options_signal_exceptions import (
    OptionValueValidationError,
)


def validate_is_datetime(value: str):
    """Validate that the value is a valid datetime string in ISO 8601 format."""

    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise OptionValueValidationError(
            message="The provided value is not a valid ISO 8601 datetime string.",
        ) from None


def validate_is_uuid4(value: str):
    """Validate that the value is a valid, hyphenated UUID4 string.

    Non-hyphenated UUID4 strings are considered invalid.
    """

    try:
        val = uuid.UUID(value, version=4)
        if str(val) != value:
            raise OptionValueValidationError(
                message=(
                    "While the provided value is a valid UUID4 string, it failed "
                    "validation due to incorrect formatting (expected hyphenated "
                    "format)."
                ),
            )
    except ValueError:
        raise OptionValueValidationError(
            message="The provided value is not a valid UUID4 string.",
        ) from None


def validate_is_ip_address(value: str):
    """Validate that the value is a valid IP address."""

    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise OptionValueValidationError(
            message="The provided value is not a valid IP address.",
        ) from None


def validate_is_cidr(value: str):
    """Validate that the value is a valid CIDR subnet."""

    try:
        ipaddress.ip_network(value)
    except ValueError:
        raise OptionValueValidationError(
            "The provided value is not a valid CIDR subnet."
        ) from None


def validate_is_url(value: str):
    """Validate that the value is a valid URL with a defined scheme and network location."""

    try:
        parsed = urlparse(value)
        if not all([parsed.scheme, parsed.netloc]):
            raise OptionValueValidationError(
                message=(
                    "The provided value is not a valid URL it is missing at least one "
                    "of the scheme or network location."
                ),
            )
    except ValueError:
        raise OptionValueValidationError(
            message="The provided value is not a valid URL.",
        ) from None


def validate_is_http_url(value: str):
    """Validate that the value is a valid HTTP or HTTPS URL."""

    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise OptionValueValidationError(
            "The provided value is not a valid http or https URL with a valid host."
        )


def validate_is_url_path(value: str):
    """Validate that the value is a valid URL endpoint path."""

    if not value.startswith("/"):
        raise OptionValueValidationError("The URL path provided must start with '/'")

    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        raise OptionValueValidationError(
            "Expected a relative path for the provided value, but received a full URL."
        )

    if parsed.query or parsed.fragment:
        raise OptionValueValidationError(
            "The URL path provided should not include query parameters or fragments."
        )

    url_path_regex = re.compile(
        r"^/(?:[a-zA-Z0-9._~!\$&\'\(\)\*\+,;=:@/-]|%[0-9a-fA-F]{2})*$"
    )
    if not url_path_regex.match(value):
        raise OptionValueValidationError(
            "The provided value contains illegal URL characters."
        )


def validate_is_filesystem_path_and_exists(value: str):
    """Validate that the value is a valid filesystem path that exists."""

    try:
        pathlib.Path(value)
        if not pathlib.Path(value).exists():
            raise OptionValueValidationError(
                message="The provided filesystem path does not exist.",
            )
    except Exception:
        raise OptionValueValidationError(
            message="The provided value is not a valid filesystem path.",
        ) from None


def validate_is_file_and_exists(value: str):
    """Validate that the value is a valid filesystem path to a file that exists."""

    try:
        pathlib.Path(value)
        if not pathlib.Path(value).is_file():
            raise OptionValueValidationError(
                message="The provided filesystem path is not a file that exists.",
            )
    except Exception:
        raise OptionValueValidationError(
            message="The provided value is not a valid filesystem path.",
        ) from None


def validate_is_directory_and_exists(value: str):
    """Validate that the value is a valid filesystem path to a directory that exists."""

    try:
        pathlib.Path(value)
        if not pathlib.Path(value).is_dir():
            raise OptionValueValidationError(
                message="The provided filesystem path is not a directory that exists.",
            )
    except Exception:
        raise OptionValueValidationError(
            message="The provided value is not a valid filesystem path.",
        ) from None
