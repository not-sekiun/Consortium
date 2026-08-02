import os
import pathlib
import uuid
from collections.abc import AsyncIterator

from rich.progress import Progress


# Streams a downloaded repository resource (an asset, artifact or payload) to
# `output_file_path`, reporting progress against `total_size_bytes`.
#
# The stream is written to a temporary file beside the destination and moved into place
# only once it has completed, rather than being written to the destination directly.
# Opening the destination truncates it immediately, which happens before a single byte
# of the response has been requested: `resource_stream` is an async generator, so the
# request is only issued when it is first iterated below. A download that then fails
# (an API error, or a connection dropped part way through) would leave the operator
# with nothing at a path that previously held a good file. The temporary file is
# created in the destination's own directory so that the move is a rename within one
# filesystem rather than a copy, and is removed again if anything goes wrong.
async def download_resource_stream_to_file(
    resource_stream: AsyncIterator[bytes],
    output_file_path: pathlib.Path,
    total_size_bytes: int | None = None,
) -> None:
    temp_file_path = output_file_path.with_name(
        f".{output_file_path.name}.{uuid.uuid4().hex}.partial",
    )

    try:
        with Progress(transient=True) as progress:
            downloading_task = progress.add_task("", total=total_size_bytes)
            # Opened exclusively so that the download can never write over an
            # unrelated file that happens to already sit at the temporary path.
            with temp_file_path.open("xb") as temp_file:
                async for chunk in resource_stream:
                    progress.update(downloading_task, advance=len(chunk))
                    temp_file.write(chunk)
        # Overwriting the destination is the caller's decision: it is expected to have
        # confirmed the overwrite before starting the download.
        os.replace(temp_file_path, output_file_path)
    # `BaseException` rather than `Exception` so that the partial file is cleaned up
    # when the download is cancelled or interrupted too, not only when it errors.
    except BaseException:
        temp_file_path.unlink(missing_ok=True)
        raise
