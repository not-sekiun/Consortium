from typing import Any, Callable

from prompt_toolkit import ANSI, print_formatted_text


def color_black(output: str | bytes, bold: bool = False, dim: bool = False) -> str:
    if bold:
        return f"\x1b[30;1m{output}\x1b[0m"
    elif dim:
        return f"\x1b[30;2m{output}\x1b[0m"
    else:
        return f"\x1b[30m{output}\x1b[0m"


def color_red(output: str | bytes, bold: bool = False, dim: bool = False) -> str:
    if bold:
        return f"\x1b[31;1m{output}\x1b[0m"
    elif dim:
        return f"\x1b[31;2m{output}\x1b[0m"
    else:
        return f"\x1b[31m{output}\x1b[0m"


def color_green(output: str | bytes, bold: bool = False, dim: bool = False) -> str:
    if bold:
        return f"\x1b[32;1m{output}\x1b[0m"
    elif dim:
        return f"\x1b[32;2m{output}\x1b[0m"
    else:
        return f"\x1b[32m{output}\x1b[0m"


def color_yellow(output: str | bytes, bold: bool = False, dim: bool = False) -> str:
    if bold:
        return f"\x1b[33;1m{output}\x1b[0m"
    elif dim:
        return f"\x1b[33;2m{output}\x1b[0m"
    else:
        return f"\x1b[33m{output}\x1b[0m"


def color_blue(output: str | bytes, bold: bool = False, dim: bool = False) -> str:
    if bold:
        return f"\x1b[34;1m{output}\x1b[0m"
    elif dim:
        return f"\x1b[34;2m{output}\x1b[0m"
    else:
        return f"\x1b[34m{output}\x1b[0m"


def color_magenta(output: str | bytes, bold: bool = False, dim: bool = False) -> str:
    if bold:
        return f"\x1b[35;1m{output}\x1b[0m"
    elif dim:
        return f"\x1b[35;2m{output}\x1b[0m"
    else:
        return f"\x1b[35m{output}\x1b[0m"


def color_cyan(output: str | bytes, bold: bool = False, dim: bool = False) -> str:
    if bold:
        return f"\x1b[36;1m{output}\x1b[0m"
    elif dim:
        return f"\x1b[36;2m{output}\x1b[0m"
    else:
        return f"\x1b[36m{output}\x1b[0m"


def color_white(output: str | bytes, bold: bool = False, dim: bool = False) -> str:
    if bold:
        return f"\x1b[37;1m{output}\x1b[0m"
    elif dim:
        return f"\x1b[37;2m{output}\x1b[0m"
    else:
        return f"\x1b[37m{output}\x1b[0m"


def print_black(
    *args: str | bytes,
    bold: bool = False,
    dim: bool = False,
    **kwargs: Any,
) -> None:
    print_formatted_text(
        *[ANSI(color_black(arg, bold=bold, dim=dim)) for arg in args],
        **kwargs,
    )


def print_red(
    *args: str | bytes,
    bold: bool = False,
    dim: bool = False,
    **kwargs: Any,
) -> None:
    print_formatted_text(
        *[ANSI(color_red(arg, bold=bold, dim=dim)) for arg in args],
        **kwargs,
    )


def print_green(
    *args: str | bytes,
    bold: bool = False,
    dim: bool = False,
    **kwargs: Any,
) -> None:
    print_formatted_text(
        *[ANSI(color_green(arg, bold=bold, dim=dim)) for arg in args],
        **kwargs,
    )


def print_yellow(
    *args: str | bytes,
    bold: bool = False,
    dim: bool = False,
    **kwargs: Any,
) -> None:
    print_formatted_text(
        *[ANSI(color_yellow(arg, bold=bold, dim=dim)) for arg in args],
        **kwargs,
    )


def print_blue(
    *args: str | bytes,
    bold: bool = False,
    dim: bool = False,
    **kwargs: Any,
) -> None:
    print_formatted_text(
        *[ANSI(color_blue(arg, bold=bold, dim=dim)) for arg in args],
        **kwargs,
    )


def print_magenta(
    *args: str | bytes,
    bold: bool = False,
    dim: bool = False,
    **kwargs: Any,
) -> None:
    print_formatted_text(
        *[ANSI(color_magenta(arg, bold=bold, dim=dim)) for arg in args],
        **kwargs,
    )


def print_cyan(
    *args: str | bytes,
    bold: bool = False,
    dim: bool = False,
    **kwargs: Any,
) -> None:
    print_formatted_text(
        *[ANSI(color_cyan(arg, bold=bold, dim=dim)) for arg in args],
        **kwargs,
    )


def print_white(
    *args: str | bytes,
    bold: bool = False,
    dim: bool = False,
    **kwargs: Any,
) -> None:
    print_formatted_text(
        *[ANSI(color_white(arg, bold=bold, dim=dim)) for arg in args],
        **kwargs,
    )


def print_success(*args: str | bytes, color: bool = True, **kwargs: Any) -> None:
    if color:
        print_formatted_text(
            ANSI(f"{color_green('[+]', bold=True)} {args[0]}"),
            *[ANSI(arg) for arg in args[1:]],
            **kwargs,
        )
    else:
        print_formatted_text(f"[+] {args[0]}", *args[1:], **kwargs)


def print_error(*args: str | bytes, color: bool = True, **kwargs: Any) -> None:
    if color:
        print_formatted_text(
            ANSI(f"{color_red('[-]', bold=True)} {args[0]}"),
            *[ANSI(arg) for arg in args[1:]],
            **kwargs,
        )
    else:
        print_formatted_text(f"[-] {args[0]}", *args[1:], **kwargs)


def print_warning(*args: str | bytes, color: bool = True, **kwargs: Any) -> None:
    if color:
        print_formatted_text(
            ANSI(f"{color_yellow('[!]', bold=True)} {args[0]}"),
            *[ANSI(arg) for arg in args[1:]],
            **kwargs,
        )
    else:
        print_formatted_text(f"[+] {args[0]}", *args[1:], **kwargs)


def print_info(*args: str | bytes, color: bool = True, **kwargs: Any) -> None:
    if color:
        print_formatted_text(
            ANSI(f"{color_blue('[*]', bold=True)} {args[0]}"),
            *[ANSI(arg) for arg in args[1:]],
            **kwargs,
        )
    else:
        print_formatted_text(f"[*] {args[0]}", *args[1:], **kwargs)


def print_plain(
    *args: str | bytes,
    color: bool = True,
    **kwargs: Any,
) -> None:  # plain is thread safe printing and will auto print above the prompt
    if color:
        print_formatted_text(*map(ANSI, args), **kwargs)
    else:
        print_formatted_text(*args, **kwargs)


def print_indented(
    *args: str | bytes,
    indent_level: int = 1,
    print_func: Callable = print_plain,
    color: bool = True,
    **kwargs: Any,
) -> None:
    if color:
        print_formatted_text(
            ANSI(f"{color_white(' | ' * indent_level, bold=True)}"),
            end="",
        )
        print_func(*args, **kwargs)
    else:
        print_formatted_text(ANSI(f"{' | ' * indent_level}"), end="")
        print_func(*args, color=False, **kwargs)
