"""Shared type aliases used across the framework.

These aliases describe the small set of scalar and JSON-compatible value types that
framework components (options, capabilities, messages, and serialized output) accept
and produce. Import them from this module wherever a component needs to annotate a
value that must remain JSON-serializable.
"""

Primitive = str | int | float | bool
"""A single scalar value: `str`, `int`, `float`, or `bool`."""

PrimitiveCollection = list[Primitive] | dict[str, Primitive]
"""A flat collection of primitives: either a list of primitives or a string-keyed
mapping of primitives."""

JSON = Primitive | list["JSON"] | dict[str, "JSON"]
"""Any JSON-serializable value: a primitive, or an arbitrarily nested list or
string-keyed mapping of JSON values."""

JSONObject = dict[str, JSON]
"""A JSON object: a string-keyed mapping whose values are any JSON-serializable value."""

PrimitiveType = type[str] | type[int] | type[float] | type[bool]
"""One of the primitive types themselves (the `str`, `int`, `float`, or `bool` class),
used to declare the expected value type of an option."""
