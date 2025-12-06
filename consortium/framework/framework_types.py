Primitive = str | int | float | bool
PrimitiveCollection = list[Primitive] | dict[str, Primitive]
JSON = Primitive | list["JSON"] | dict[str, "JSON"]
JSONObject = dict[str, JSON]
PrimitiveType = type[str] | type[int] | type[float] | type[bool]
