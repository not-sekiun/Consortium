import asyncio
import io
import os
import pathlib
import uuid
import zipfile
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import contextmanager
from typing import IO

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


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


# Shared by every operation below so that the phases of a single command (archiving a
# directory, then uploading it) are rendered identically. The spinner is what
# distinguishes work that is still running from a display that has stalled, which
# matters for the phases whose progress cannot be measured: the walk of a directory
# before its total size is known, and the wait for the server's response after the last
# byte of an upload has been sent.
def _create_transfer_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        transient=True,
    )


# Wraps the file object handed to the REST API client so that an upload can be reported
# while it happens. Nothing in the upload path offers a progress callback: aiohttp
# streams a file payload by reading it in fixed size chunks and writing each one to the
# connection, so those reads are the only progress signal available to the client, and a
# read returning means the chunk before it has been written out.
#
# `io.IOBase` is subclassed rather than the file object simply being held by a plain
# wrapper because aiohttp chooses how to serialize a form field from the value's type,
# and rejects anything it does not recognise as file like. `fileno` and `tell` are
# delegated because the request's Content-Length is derived from them, and `name`
# because the multipart filename is taken from it: without them the upload would change
# shape on the wire rather than just gain a progress bar.
#
# `close` is deliberately not delegated. The underlying file object belongs to the
# caller, which opened it and closes it itself.
class _ProgressReportingFileReader(io.IOBase):
    def __init__(
        self,
        file_object: IO[bytes],
        report_progress: Callable[[int], None],
    ):
        self._file_object = file_object
        self._report_progress = report_progress
        self._start_position = file_object.tell()
        self._bytes_read = 0

    @property
    def name(self) -> str:
        return self._file_object.name

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return self._file_object.seekable()

    def read(self, size: int = -1) -> bytes:
        chunk = self._file_object.read(size)
        self._bytes_read += len(chunk)
        self._report_progress(self._bytes_read)
        return chunk

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        position = self._file_object.seek(offset, whence)
        # aiohttp seeks the payload back to its starting position when it has to send
        # the body a second time (following a redirect), so the count is rebased on the
        # position seeked to rather than being left to climb from a total that no longer
        # reflects what is actually being sent.
        self._bytes_read = max(position - self._start_position, 0)
        self._report_progress(self._bytes_read)
        return position

    def tell(self) -> int:
        return self._file_object.tell()

    def fileno(self) -> int:
        return self._file_object.fileno()


# Yields a stand in for `file_object` that reports its own progress as an uploading
# REST API client reads it, against a `total_size_bytes` the caller is expected to have
# taken from the file on disk.
#
# The request itself is made by the caller inside the `with` block so that the display
# stays up for the whole operation, including the wait for the response.
@contextmanager
def report_resource_upload_progress(
    file_object: IO[bytes],
    total_size_bytes: int | None = None,
    description: str = "Uploading",
) -> Iterator[IO[bytes]]:
    with _create_transfer_progress() as progress:
        upload_progress_task = progress.add_task(description, total=total_size_bytes)

        # What is counted here is the bytes written to the connection, which is the
        # closest the client can get to upload progress: the server sends nothing back
        # until it has received the whole body, stored the resource and checksummed it.
        # The description is switched at the last chunk so that the wait for that
        # response, which is not brief for a large upload, does not read as a progress
        # bar stuck at 100%.
        #
        # This runs on the executor thread aiohttp reads the payload on rather than on
        # the event loop, which is safe only because updating a `Progress` is guarded by
        # a lock internally.
        def report_progress(uploaded_size_bytes: int) -> None:
            progress.update(upload_progress_task, completed=uploaded_size_bytes)
            if total_size_bytes is not None and uploaded_size_bytes >= total_size_bytes:
                progress.update(
                    upload_progress_task,
                    description="Waiting for the server to process the upload",
                )

        yield _ProgressReportingFileReader(
            file_object=file_object,
            report_progress=report_progress,
        )


def _archive_directory(
    directory_path: pathlib.Path,
    output_archive_file_path: pathlib.Path,
    report_total_size: Callable[[int], None],
    report_progress: Callable[[int], None],
) -> None:
    # The directory is walked in full before anything is written so that the size of the
    # work is known up front: without a total there is no progress to report, only a
    # count of bytes that means nothing on its own. Sizes are recorded during the walk
    # rather than being stated again per file while archiving.
    directory_paths: list[pathlib.Path] = []
    file_paths_and_sizes: list[tuple[pathlib.Path, int]] = []
    for entry_path in directory_path.rglob("*"):
        if entry_path.is_dir():
            directory_paths.append(entry_path)
        elif entry_path.is_file():
            file_paths_and_sizes.append((entry_path, entry_path.stat().st_size))
    report_total_size(sum(size for _, size in file_paths_and_sizes))

    archived_size_bytes = 0
    with zipfile.ZipFile(
        output_archive_file_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive_file:
        # Every directory is given an entry of its own, as `shutil.make_archive` does,
        # so that directories that hold no files still survive the round trip through
        # the archive.
        for archived_directory_path in directory_paths:
            archive_file.write(
                archived_directory_path,
                arcname=archived_directory_path.relative_to(directory_path),
            )
        for archived_file_path, archived_file_size_bytes in file_paths_and_sizes:
            archive_file.write(
                archived_file_path,
                arcname=archived_file_path.relative_to(directory_path),
            )
            archived_size_bytes += archived_file_size_bytes
            report_progress(archived_size_bytes)


# Archives the contents of `directory_path` into `output_archive_file_path` as a zip
# file, reporting progress as it goes.
#
# `shutil.make_archive` does the same job in a single call, but only synchronously.
# Called from a command it compresses the whole directory on the client's event loop,
# which stops the REPL dead (along with every event hook and keystroke) for as long as
# that takes and reports nothing at all while it runs, so a large directory looks like
# a hang before its upload has even started. The work is handed to a worker thread here
# instead, leaving the event loop free to render the progress of the archiving.
#
# Progress is measured in uncompressed bytes archived, so it advances a file at a time:
# a directory of one enormous file reports far more coarsely than a directory of many
# small ones.
async def archive_directory_to_file(
    directory_path: pathlib.Path,
    output_archive_file_path: pathlib.Path,
    description: str = "Archiving directory",
) -> None:
    with _create_transfer_progress() as progress:
        # Started without a total, which renders as an indeterminate bar, because the
        # directory's size is not known until it has been walked.
        archive_progress_task = progress.add_task(description, total=None)

        def report_total_size(total_size_bytes: int) -> None:
            progress.update(archive_progress_task, total=total_size_bytes)

        def report_progress(archived_size_bytes: int) -> None:
            progress.update(archive_progress_task, completed=archived_size_bytes)

        await asyncio.to_thread(
            _archive_directory,
            directory_path,
            output_archive_file_path,
            report_total_size,
            report_progress,
        )
