from typing import Any


def remap_exception(
    original_exception: Exception,
    original_kwargs: dict[str, Any],
    exception_map: dict[type[Exception], type[Exception]],
    exception_kwargs_map: dict[str, str],
) -> BaseException:
    remapped_kwargs = {
        exception_kwargs_map.get(k, k): v for k, v in original_kwargs.items()
    }
    remapped_exception_class = exception_map[type(original_exception)]
    return remapped_exception_class(**remapped_kwargs)
