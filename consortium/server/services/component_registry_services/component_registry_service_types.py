from typing import TypeVar

from consortium.framework._core.components import ComponentMetadata

Component = TypeVar("Component", bound=ComponentMetadata)
ComponentLoadingError = TypeVar("ComponentLoadingError")
