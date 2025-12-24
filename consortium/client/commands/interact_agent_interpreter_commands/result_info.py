# from argparse import ArgumentParser
#
# from consortium.client.commands.agents_interpreter_commands import (
#     ResultInfoCommand as ResultInfoAgentsInterpreterCommand,
# )
# from consortium.client.objects.client_return_status_objects import (
#     ClientReturnStatusType,
# )
# from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
# from consortium.client.utils.formatter_utils import format_argparse_epilog
#
#
# class ResultInfoCommand(ResultInfoAgentsInterpreterCommand):
#     name = "result_info"
#     description = (
#         "Display detailed information about a specific agent result for the currently "
#         "selected agent being interacted with."
#     )
#     epilog = format_argparse_epilog(
#         """
#         Examples:
#             result_info 43e56f0b-c3d2-4c70-82a9-8d27ded2cb2f  # Display detailed information about a specific result for the currently selected agent being interacted with.
#         """,
#     )
#     group = "Tasks and Results Management Commands"
#
#     def configure_parser(self, parser: ArgumentParser) -> None:
#         parser.add_argument(
#             "result_id",
#             help="The result ID of the result to display detailed information for.",
#             type=str,
#         )
#
#     async def run_command(
#         self,
#         command_context: CommandContext,
#     ) -> ReturnStatus:
#         try:
#             parsed_args = self.parser.parse_args(command_context.arguments)
#             client_rest_api_connection = command_context.environment[
#                 "client_rest_api_connection"
#             ]
#             await self._display_result_info_from_agent_id(
#                 client_rest_api_connection=client_rest_api_connection,
#                 agent_id=command_context.environment["agent"]["agent_id"],
#                 result_id=parsed_args.result_id,
#             )
#         except SystemExit:
#             pass
#
#         return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
