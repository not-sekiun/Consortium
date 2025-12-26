import ipaddress
import pathlib
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse

from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)


def validate_is_datetime(value: str):
    """
    Validates if the provided value to the option is a valid datetime string in ISO
    8601 format.
    """

    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise OptionValueValidationError(
            message="The provided value is not a valid ISO 8601 datetime string.",
        ) from None


def validate_is_uuid4(value: str):
    """
    Validates if the provided value to the option is a valid UUID4 string. Note that
    non-hyphenated UUID4 strings are considered invalid.
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
    """
    Validates if the provided value to the option is a valid IP address.
    """

    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise OptionValueValidationError(
            message="The provided value is not a valid IP address.",
        ) from None


def validate_is_cidr(value: str):
    """
    Validates if the provided value to the option is a valid CIDR subnet.
    """

    try:
        ipaddress.ip_network(value)
    except ValueError:
        raise OptionValueValidationError(
            "The provided value is not a valid CIDR subnet."
        ) from None


def validate_is_url(value: str):
    """
    Validates if the provided value to the option is a valid URL with a defined scheme
    and network location.
    """

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
    """
    Validates if the provided value to the option is a valid HTTP or HTTPS URL.
    """

    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise OptionValueValidationError(
            "The provided value is not a valid http or https URL with a valid host."
        )


def validate_is_url_path(value: str):
    """
    Validates if the provided value to the option is a valid URL endpoint path.
    """

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
    """
    Validates if the provided value to the option is a valid filesystem path and that
    the path exists.
    """

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
    """
    Validates if the provided value to the option is a valid filesystem path and that
    the path is a file that exists.
    """

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
    """
    Validates if the provided value to the option is a valid filesystem path and that
    the path is a directory that exists.
    """

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
