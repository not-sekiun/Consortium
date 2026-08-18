# How much memory agent task message data may occupy. The two limits are kept together
# because they are only coherent in relation to one another, and the invariant tying them
# together is enforced by `validate_size_limits` rather than left implicit:
#
#     SPOOL_TO_DISK_ABOVE  <  QUEUE_MEMORY_LIMIT
#
# A payload under the threshold is resident and counts against a queue's budget, so a
# threshold above the limit means a single payload does not fit and the queue admits it
# only through its one-time oversize exception, then blocks. Keeping the threshold at an
# eighth of the limit lets eight max-resident payloads coexist before backpressure.

# Per-queue (inbox or outbox) budget for resident in-flight message data before a producer
# is back-pressured. Payloads spilled to disk do not count against it.
#
# Sized to the burst a task produces, not to buffering depth: throughput is set by how fast
# the consumer drains, so depth past the burst size trades memory for staleness rather than
# throughput. 4 MB holds ~136 process listings or ~1,860 shell outputs for one task.
#
# Not a server-wide bound. Every task holds an inbox and an outbox, so resident worst case
# is concurrent_tasks * 2 * this.
QUEUE_MEMORY_LIMIT = 4 * 1024 * 1024

# The line between a payload kept in memory and one spilled to a temporary file. At or
# below this a received payload stays resident; above it, it rolls over to disk.
SPOOL_TO_DISK_ABOVE = 512 * 1024


def validate_size_limits(
    *,
    queue_memory_limit: int = QUEUE_MEMORY_LIMIT,
    spool_to_disk_above: int = SPOOL_TO_DISK_ABOVE,
) -> None:
    # Fail loudly if a combination of sizes violates the invariant, so an incoherent
    # retune surfaces at construction time rather than as a deadlocked queue at runtime.
    if spool_to_disk_above >= queue_memory_limit:
        raise ValueError(
            f"spool_to_disk_above ({spool_to_disk_above}) must be less than "
            f"queue_memory_limit ({queue_memory_limit}); otherwise a resident payload "
            f"cannot fit in a queue's memory budget."
        )


# The limits above are checked against each other once, here, so an incoherent edit fails
# at import rather than at the first queue that deadlocks on it. Anything overriding them
# calls this with its own values.
validate_size_limits()
