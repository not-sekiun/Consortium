from argparse import Namespace

from consortium.client.commands.agents_interpreter_commands import (
    TaskCommand as TaskAgentsInterpreterCommand,
)
from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class TaskCommand(TaskAgentsInterpreterCommand):
    description = "Manage the current agent's tasks through its sub-commands"
    epilog = format_argparse_epilog(
        """
        Examples:
          task list
          task info 123e4567-e89b-12d3-a456-426614174000
          task watch 123e4567-e89b-12d3-a456-426614174000
          task delete 123e4567-e89b-12d3-a456-426614174000

        Notes:
          Every sub-command carries its own help, for example:
            task info --help
        """,
    )
    list_help = (
        "List all tasks for the current agent, or for a specific agent by its ID."
    )
    list_agent_id_help = (
        "ID of the agent to list tasks for (defaults to the current agent if not "
        "provided)."
    )
    list_epilog = format_argparse_epilog(
        """
        Examples:
          task list  # If no filters are provided, list all tasks for the current agent being interacted with regardless of status.
          task list --running --completed
            # Lists RUNNING plus terminal SUCCEEDED, FAILED, and ERRORED tasks.
          task list 123e4567-e89b-12d3-a456-426614174000
        """,
    )

    # Only the listing differs from the agents interpreter's task command: with no agent
    # ID it lists the tasks of the agent being interacted with rather than those of
    # every agent.
    async def _handle_list_sub_command(
        self,
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        if parsed_args.agent_id:
            agent = await rest_api.get_agent_by_agent_id(
                agent_id=parsed_args.agent_id,
            )
        else:
            agent = context.interpreter_context.agent

        agent_tasks = await self._get_tasks_to_list(
            rest_api=rest_api,
            agent_id=agent["agent_id"],
            display_queued=parsed_args.queued,
            display_running=parsed_args.running,
            display_completed=parsed_args.completed,
        )
        commands_to_required_arguments_map = (
            await self._compute_agent_commands_to_required_arguments_map(
                agent=agent,
            )
        )
        self._list_tasks(
            agent_id=agent["agent_id"],
            agent_name=agent["name"],
            agent_tasks=agent_tasks,
            commands_to_required_arguments_map=commands_to_required_arguments_map,
        )

        return ContinueSignal()
