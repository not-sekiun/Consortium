# from consortium.server.framework.c2_types import ListenerType
# from consortium.server.framework.base_listener_template import BaseListenerTemplate
# from consortium.server.framework.base_listener import BaseListener
# from consortium.server.framework.options import SingleValueOption
#
#
# MY_LISTENER_TYPE = ListenerType(
#     name="MyListenerType",
# )
#
#
# class MyListener(BaseListener):
#     listener_type = MY_LISTENER_TYPE
#
#     def on_listener_started(self) -> None: ...
#
#     def on_listener_stopped(self) -> None: ...
#
#     def on_listener_error(self, error: Exception) -> None: ...
#
#     def on_listener_running(self) -> None: ...
#
#     def on_listener_cancelled(self) -> None: ...
#
#
# class MyListenerTemplate(BaseListenerTemplate):
#     listener = MyListener
#     name = "MyListenerTemplate"
#     description = "My listener template description"
#     options = [
#         SingleValueOption(
#             name="name",
#             description="The name of the listener.",
#             required=True,
#             value_type=str,
#         ),
#         SingleValueOption(
#             name="local_host",
#             description="The local host address to listen on.",
#             required=True,
#             value_type=str,
#         ),
#         SingleValueOption(
#             name="local_port",
#             description="The local port number to listen on.",
#             required=True,
#             value_type=int,
#             validating_function=lambda value: 0 <= value <= 65535,
#         ),
#     ]
#
#     def resolve_listener_endpoint(self) -> str:
#         local_host = self.get_option_by_option_name("local_host").get_option_value()
#         local_port = self.get_option_by_option_name("local_port").get_option_value()
#         return f"{local_host}:{local_port}"
#
#     def resolve_listener_name(self) -> str:
#         return self.get_option_by_option_name("name").get_option_value()
#
#
# my_listener_template = MyListenerTemplate()
# print(repr(my_listener_template))


from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.framework.options import SingleValueOption


def validate_positive(value: int):
    if value < 0:
        raise OptionValueValidationError("Value must be greater than 0")


option = SingleValueOption(
    name="test",
    description="Test option",
    required=True,
    value_type=int,
    validating_function=validate_positive,
    default_value=-1,
)
