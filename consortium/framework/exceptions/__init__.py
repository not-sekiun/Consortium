"""
The exceptions defined here are known as "signalling" exceptions. They are used to
signal some kind of error condition either from within a framework component to the
calling framework or to explicitly handle an error condition that arose from the
calling framework within a framework component.
"""

from consortium.framework.exceptions.base_framework_exception import (
    BaseCatchOnlyFrameworkException,
    BaseFrameworkException,
    BaseRaiseOnlyFrameworkException,
)

__all__ = [
    "BaseFrameworkException",
    "BaseRaiseOnlyFrameworkException",
    "BaseCatchOnlyFrameworkException",
]
