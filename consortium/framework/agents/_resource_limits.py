# How much memory and disk agent task message data may occupy. The three limits are kept
# together because they are only coherent in relation to one another, and the invariant
# tying them together is enforced by `validate_size_limits` rather than left implicit:
#
#     SPOOL_TO_DISK_ABOVE  <  QUEUE_MEMORY_LIMIT
#     SPOOL_TO_DISK_ABOVE  <  MAX_PAYLOAD_SIZE
#
# Spill threshold below the queue limit: a payload under the threshold is resident and
# counts against a queue's budget, so a threshold above the limit means a single payload
# does not fit and the queue admits it only through its one-time oversize exception, then
# blocks. Keeping the threshold at an eighth of the limit lets eight max-resident payloads
# coexist before backpressure.
#
# Spill threshold below the payload cap: anything above the threshold spills to disk and
# stops counting against queue memory, which is why the cap is allowed to exceed the queue
# limit. At or above the cap, payloads would never spill and a cap-sized upload would sit
# fully resident.
#
# Rule of thumb when retuning: spill threshold at an eighth of the queue limit, payload cap
# from what a capability can afford to materialize (see the caveat on MAX_PAYLOAD_SIZE).

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

# The largest single payload a transport will accept. Enforced as bytes arrive so an
# oversized upload is rejected mid-stream, and attributable: one agent sending too much is
# that agent's fault, and chunking (the upload capability's `chunk_size`) is its remedy.
#
# Caveat on treating this as purely a disk bound: a spilled payload costs a file descriptor
# and disk rather than resident memory, but `Payload.load()` buffers a whole stream into
# memory, outside any queue's accounting. So set this from what a single capability can
# afford to materialize, not from disk alone.
MAX_PAYLOAD_SIZE = 64 * 1024 * 1024


def validate_size_limits(
    *,
    queue_memory_limit: int = QUEUE_MEMORY_LIMIT,
    spool_to_disk_above: int = SPOOL_TO_DISK_ABOVE,
    max_payload_size: int | None = MAX_PAYLOAD_SIZE,
) -> None:
    # Fail loudly if a combination of sizes violates the invariant, so an incoherent
    # retune surfaces at construction time rather than as a deadlocked queue at runtime.
    # A None payload cap means unbounded, so the second check does not apply.
    if spool_to_disk_above >= queue_memory_limit:
        raise ValueError(
            f"spool_to_disk_above ({spool_to_disk_above}) must be less than "
            f"queue_memory_limit ({queue_memory_limit}); otherwise a resident payload "
            f"cannot fit in a queue's memory budget."
        )
    if max_payload_size is not None and spool_to_disk_above >= max_payload_size:
        raise ValueError(
            f"spool_to_disk_above ({spool_to_disk_above}) must be less than "
            f"max_payload_size ({max_payload_size}); otherwise a cap-sized payload never "
            f"spills to disk and sits fully resident."
        )


# The limits above are checked against each other once, here, so an incoherent edit fails
# at import rather than at the first queue that deadlocks on it. Anything overriding them
# calls this with its own values.
validate_size_limits()
