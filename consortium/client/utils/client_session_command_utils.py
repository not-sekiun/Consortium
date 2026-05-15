import uuid

import consortium.client.client_singletons as client_singletons
from consortium.client.utils.printer_utils import print_error, print_success, console
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionNotFoundError,
)
from consortium.client.utils.formatter_utils import (
    format_datetime_as_human_readable_str,
    format_role_str_with_color,
)

from rich.table import Table

client_sessions_service = client_singletons.client_sessions_service


def describe_client_session(
    client_session_id: str | uuid.UUID,
    description: str,
) -> None:
    try:
        client_session = (
            client_sessions_service.get_client_session_by_client_session_id(
                client_session_id=client_session_id,
            )
        )
    except ClientSessionNotFoundError as exc:
        print_error(str(exc))
        return

    client_session.description = description
    print_success(
        f"Updated {client_session} description to '{client_session.description}'"
    )


async def display_client_session_info(
    client_session_id: str | uuid.UUID,
    show_password: bool,
) -> None:
    try:
        client_session = (
            client_sessions_service.get_client_session_by_client_session_id(
                client_session_id=client_session_id,
            )
        )
    except ClientSessionNotFoundError as exc:
        print_error(str(exc))
        return

    own_user_info = await client_session.rest_api.get_own_user_info()
    server_release = await client_session.rest_api.get_server_release()

    table = Table(title="Client Session Information", highlight=True)
    table.add_column("Information")
    table.add_column("Data")
    table.add_row(
        "Client Session ID",
        str(client_session.client_session_id),
    )
    table.add_row("Name", client_session.name)
    table.add_row("Description", client_session.description)
    table.add_row("Username", client_session.username)
    table.add_row("Password", client_session.password if show_password else "********")
    table.add_row("Remote Host", client_session.remote_host)
    table.add_row("Remote Port", str(client_session.remote_port))
    table.add_row("Role", format_role_str_with_color(role=own_user_info["role"]))
    table.add_row("Connected", str(client_session.connected))
    table.add_row(
        "Datetime Connected",
        format_datetime_as_human_readable_str(
            datetime_str=client_session.datetime_connected,
            include_elapsed_time=True,
        ),
    )
    table.add_row(
        "Server Release",
        f"v{server_release['version']} ({server_release['codename']}) released "
        f"{format_datetime_as_human_readable_str(datetime_str=server_release['datetime_released'])}",
    )
    console.print(table, "")


def rename_client_session(client_session_id: str | uuid.UUID, name: str) -> None:
    try:
        client_session = (
            client_sessions_service.get_client_session_by_client_session_id(
                client_session_id=client_session_id,
            )
        )
    except ClientSessionNotFoundError as exc:
        print_error(str(exc))
        return

    # Store the previous client session string for the success
    # message to demonstrate the change in name.
    previous_client_session_str = str(client_session)
    client_session.name = name
    print_success(
        f"Renamed client session {previous_client_session_str} to '{client_session.name}'"
    )
