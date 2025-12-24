# from argparse import ArgumentParser
#
# from consortium.client.commands.agents_interpreter_commands import (
#     TaskInfoCommand as TaskInfoAgentInterpretersCommand,
# )
# from consortium.client.objects.client_return_status_objects import (
#     ClientReturnStatusType,
# )
# from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
# from consortium.client.utils.formatter_utils import format_argparse_epilog
#
#
# class TaskInfoCommand(TaskInfoAgentInterpretersCommand):
#     name = "task_info"
#     description = (
#         "Display detailed information about a specific agent task for a specific "
#         "agent or for the currently selected agent being interacted with."
#     )
#     epilog = format_argparse_epilog(
#         """
#         Examples:
#             task_info 43e56f0b-c3d2-4c70-82a9-8d27ded2cb2f  # Display detailed information about a specific task for the currently selected agent being interacted with.
#             task_info 123e4567-e89b-12d3-a456-42661417400 43e56f0b-c3d2-4c70-82a9-8d27ded2cb2f  # Display detailed information about a specific task for a specific agent.
#         """,
#     )
#     group = "Tasks and Results Management Commands"
#
#     def configure_parser(self, parser: ArgumentParser) -> None:
#         parser.add_argument(
#             "agent_id",
#             help=(
#                 "The agent ID of the agent to get the information of a particular "
#                 "task for. If not provided, the agent ID of the currently selected "
#                 "agent being interacted with will be used."
#             ),
#             type=str,
#             nargs="?",
#         )
#         parser.add_argument(
#             "task_id",
#             help="The task ID of the task to display detailed information for.",
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
#             await self._display_task_info_from_agent_id_and_task_id(
#                 client_rest_api_connection=client_rest_api_connection,
#                 agent_id=parsed_args.agent_id
#                 if parsed_args.agent_id
#                 else command_context.environment["agent"]["agent_id"],
#                 task_id=parsed_args.task_id,
#             )
#         except SystemExit:
#             pass
#
#         return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
