# Ingestion

**Status: draft; not approved. Not an implementation baseline.**

This proposed block specification has received a design review but has not been
approved by the project owner. Its polling algorithms, lifecycle, and resource
policies are proposals, not consequences of approving the overall architecture.

## Responsibility and boundary

Ingestion hands source records and explicit acquisition outcomes to durable
processing. A concrete adapter obtains the records; `processing` determines when
their consequences have been accepted durably. Ingestion does not detect mail
rejection, assign event/delivery identities, execute SQL, or send notifications.

The common invariant is: **no acknowledgement of accepted input before its
necessary processing consequences are durable**. Polling, source checkpoints,
history lookup, and complete-response buffering are not mandatory capabilities of
all future input types. Only the initial VictoriaLogs polling specialization is
being considered here; no speculative adapters or universal source API are added.

## Contract concepts

These concepts describe meaning, not Go interfaces or serialized schemas.

| Concept | Contents and constraints |
| --- | --- |
| Input identity | Stable configured input ID, source scope/type, and applicable configuration revision |
| Record | Source identity, reliable source-record ID when available, source time when available, separate observation time, bounded source fields/text |
| Acquisition outcome | Records plus explicit complete/incomplete/failed result within the supported source-specific contract |
| Progress handoff | Proposed versioned source progress, bound to the committed starting state and compatible source/configuration identity |
| Failure | Bounded safe classification and operational context, not raw response data, queries, or credentials |

A record is untrusted and potentially sensitive. Its source time is not replaced
with the current time when missing. Source-record ID is not a correlation, event,
or delivery ID. Text/time hashing cannot silently invent a reliable identity.
The unresolved [source identity contract](open-decisions.md#identities-and-source-coverage)
limits what deduplication can be promised.

`complete` requires both response integrity and a verified adapter-specific
selection contract. HTTP success and syntactically valid JSON do not alone prove
that all matching records were returned. Completeness concerns the requested
selection at the time of reading, not the absence of future late arrivals.

## Proposed initial polling behavior

For the initial polling path, propose an all-or-nothing, bounded read unit:

1. Obtain the committed compatible progress and reserve shared resource capacity.
2. Ask the adapter for one bounded unit of source work.
3. Keep that unit in bounded memory until response integrity and selection
   completeness have been checked. Do not pass an incomplete prefix to detection.
4. Hand a complete unit to processing. It saves record consequences and proposed
   progress atomically, preserving the common concurrency and deduplication rules.
5. Adopt the new progress only after durable acceptance is known. Release buffers
   and reservations when ownership of the unit ends.

The tradeoff is bounded extra memory and repeated network work after interruption,
in exchange for avoiding a durable raw-record inbox and partially admitted failed
reads. This is a proposed polling strategy, not the universal ingestion contract.

An empty complete unit can advance progress. Failed or incomplete units cannot.
Previously completed units remain durable. An oversized unit can be narrowed or
split only by a source-specific method that does not skip records. If a dense
interval cannot be drained within the supported contract, it visibly blocks;
progress is not set to the maximum returned timestamp to escape the problem.

An oversized individual record or malformed transport record blocks its unit,
without clipping or silently discarding data. A well-formed record containing an
unsupported log message is different: downstream extraction records an explicit
outcome that can participate in durable acceptance.

## State ownership and recovery

- The adapter owns the meaning/version of its progress and the interpretation of
  compatible source settings. It does not independently commit progress.
- Processing owns durable admission and coordination of shared correlation
  updates. Initially, at most one polling read-and-accept operation is active per
  input. This alone does not resolve contention between different inputs.
- SQLite stores committed progress and required semantic revisions, replay
  protection, and durable downstream consequences through the processing boundary.
- Safe operational updates, such as cooldown after a failed request, can be
  committed separately. They never acknowledge records or advance progress.
- Buffers, clients, and running timers are ephemeral. Operational state needed to
  avoid restart retry storms is durable; an unbounded per-poll audit is not kept.
- Source network reads are outside SQLite transactions. Unknown commit outcomes
  are resolved from durable state, not assumed to mean rollback.

Conceptual polling lifecycle:

```text
ready -> reading -> awaiting durable acceptance -> ready
             |                   |
             +------ failure ----+--> retry wait / degraded

resource pressure -> paused
incompatible state or unresolvable read limit -> blocked
shutdown -> stopped
```

These describe observable conditions, not a proposed SQL state machine.

After restart, resume committed progress rather than resetting to a window near
the current time. A crash before durable acceptance repeats the unit; a crash
after acceptance recovers its effects and proposed progress from SQLite.
Shutdown does not manufacture successful completion of an interrupted read.

## Late arrivals, retries, and retained state

Polling uses bounded windows and configured overlap. Processed coverage and the
supported late-arrival horizon are distinct: a fully read interval may need
re-reading. No finite lookback covers arbitrarily late records.

Cleanup preserves replay protection for reads that remain supported, including
inputs paused long enough that a wall-clock TTL would otherwise remove markers.
If storage limits prevent this, losing that guarantee requires an explicit
decision rather than an ordinary resume silently becoming unprotected replay.

Each poll cycle has finite request/attempt, duration, and read-splitting budgets.
Exhaustion enters a bounded cooldown and exposes degraded status. Periodic recovery
polling may continue at a bounded rate: it is an ongoing observation activity,
not a delivery job with an indefinitely reset retry budget. Repeated ticks do not
create accumulated tasks, and retries retain the uncovered source position.
Permanent configuration or progress-compatibility failures visibly block.

Known source-history loss is reported as a gap when supported by evidence.
When historical coverage cannot be verified, report that limitation instead of
treating an empty read as proof that no records ever existed. Guarantee horizons
remain [open](open-decisions.md#identities-and-source-coverage).

Changes to source/query scope cannot silently reuse incompatible progress or
trigger history replay. Credential rotation is distinct from changing the source.
Detailed revision and replay policies belong to the
[configuration contract](open-decisions.md#configuration-and-state-compatibility).

## Context lookups

History access is a separately bound source capability, with its own bounded work
and the same source identity, cancellation, and privacy constraints. It does not
advance polling progress. Results return to the enrichment requester through
processing and the required extraction, not through unrestricted re-ingestion
that triggers unrelated rules.

A complete empty lookup means no matching data was returned now. The enrichment
owner decides whether to wait, retry, or expire. An incomplete lookup is not
evidence that the context is absent.

## Limits and exhaustion behavior

Every configured read path has finite limits. Numerical values are not approved
by this draft; see [Resource decisions](open-decisions.md#resources-retention-and-operations).

| Limit | Exhaustion behavior |
| --- | --- |
| Record bytes, field count, field/value size | Explicit failure; no lossy clipping or raw-record quarantine |
| Records and wire/decoded bytes per unit | Incomplete unit; safely narrow/split or block |
| Network timeout and total poll-cycle duration/work | Stop work; classify failure and apply bounded cooldown |
| Per-input in-flight work and global query concurrency | Defer work without accumulating tick tasks |
| Shared memory and downstream durable capacity | Reserve before reading; pause/defer rather than build an unbounded queue |
| Supported lateness and source-history retention | Expose guarantee limitations; no silent cursor reset or gap acknowledgement |

Scheduling must prevent a blocked input or repeated splitting from monopolizing
the shared resource budget. Backpressure increases visible lag; it cannot promise
that finite source retention will preserve records forever.

## Security and observability

Request only needed fields plus identity/progress evidence. Keep raw records in
bounded transient memory, not diagnostic logs or a SQLite log mirror. Record IDs,
hashes, queries, progress values, response bodies, URLs, and authentication data
are not automatically safe diagnostic fields.

Use verified TLS and least-privilege read credentials. Redirects cannot silently
forward credentials to another destination. Context parameters are escaped for
the source query language rather than concatenated as executable query fragments.

Expose last successful polling time, failures, incomplete reads, lag, limit
exhaustion, and paused/blocked conditions. Labels use bounded configured input
identities/types and error classes, never record IDs or source field values.
Validation-only does not start processing. Dry-run neither sends notifications
nor alters production progress or delivery state, including job acknowledgement.

## VictoriaLogs evidence still required

The [querying documentation](https://docs.victoriametrics.com/victorialogs/querying/)
describes streaming JSONL, unordered results by default, bounded result options,
and partial-response settings. `_stream_id` identifies a stream, not a unique log
record. A successful bounded response is not sufficient evidence of completeness
if the configured query itself limits, samples, or aggregates records.

The adapter must establish supported identity/completeness behavior for its API
and version, including query options that can override request settings. This
draft does not claim that the evidence has been established or that an adapter has
been tested. Its approval would not close the corresponding
[open decisions](open-decisions.md#identities-and-source-coverage).

## Proposed test criteria

- Complete empty reads differ from failed, truncated, malformed, and partial reads.
- An interrupted response after valid records produces no accepted unit effects
  and no progress advancement under the proposed polling strategy.
- Before/after/unknown-commit failures recover from durable state without losing
  obligations or recreating accepted events/delivery assignments.
- Replay, out-of-order records, supported lateness edges, and unsupported lateness
  exercise the declared identity and coverage boundaries.
- Distinct reliable IDs remain distinct despite identical time/text; missing
  identity does not receive an invented uniqueness guarantee.
- Oversized records, splittable windows, equal timestamps, and unresolvable dense
  intervals cannot cause silent loss, unlimited splitting, or false progress.
- Paused-input cleanup preserves the supported replay guarantee or requires an
  explicit, observable decision to change it.
- Capacity, repeated outages, restart cooldowns, and multiple inputs respect
  bounded memory/concurrency and do not create tick backlogs or retry storms.
- Source/configuration incompatibility blocks without resetting progress.
- History lookup cannot advance polling progress or trigger unrelated events.
- Dry-run leaves production state unchanged; diagnostics and metric labels do
  not disclose raw records, secrets, or record identifiers.

Tests use synthetic data, HTTP test servers, controllable time, and real temporary
SQLite databases for persistence integration. These are design criteria, not
tests that have been implemented or run.
