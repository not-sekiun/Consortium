import textwrap


# Automatically "intelligently" formats indented docstrings to a single line string by
# replacing newline characters with empty spaces if a line ends with a space or
# automatically adding a space if the newline does not end with a space.
def format_docstring_to_single_line(docstring: str) -> str:
    dedented_docstring = textwrap.dedent(docstring)
    single_line_string = ""
    for line in dedented_docstring.splitlines():
        if line.endswith(" "):
            single_line_string += line
        else:
            single_line_string += line + " "

    return single_line_string.strip()
