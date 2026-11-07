# Ingestion

**Status: approved block contract. Not implemented or conformance-verified.**

The project owner approved this block's polling protocol, lifecycle, fingerprint
policy, resource limits, and test criteria after design review. Approval does not
authorize implementation or establish that a source satisfies the required
conformance tests. Explicitly open encoding, compatibility, and cross-block
contracts remain open.

## Accepted policy inputs

The [agreed operating policies](overview.md#agreed-operating-policies) supply
fingerprint equivalence, one-hour supported lateness, finite source-read retries,
and safe error reporting. This block separately approves the polling protocol,
frontiers, and additional numeric defaults below. Message-context expiry and
business correlation belong to detection/state design, not ingestion.

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
| Record | Source view, canonical source content and replay fingerprint, source time when available, separate observation time, bounded fields/text |
| Acquisition outcome | Records plus explicit complete/incomplete/failed result within the supported source-specific contract |
| Progress handoff | Proposed versioned source progress, bound to committed starting state, coverage phase, and compatible source/configuration identity |
| Failure | Bounded safe classification and operational context, not raw response data, queries, or credentials |

A record is untrusted and potentially sensitive. Its source time is not replaced
with the current time when missing. A source's search-time coordinate can itself
be ingestion time: it does not automatically become the business event time or
relay receipt time. Missing data has an explicit outcome, not invented values.

`complete` requires both response integrity and a verified adapter-specific
selection contract. HTTP success and syntactically valid JSON do not alone prove
that all matching records were returned. Completeness concerns the requested
selection at the time of reading, not the absence of future late arrivals.

## Record fingerprint and compatibility

The accepted policy may collapse completely identical records within one source
view. It does not promise to distinguish physically separate but indistinguishable
records. Use SHA-256 over a versioned, deterministic canonical representation
of the complete authorized source row, qualified by the input/source view.

- Include original source content, source time, and stable source metadata.
  Canonicalization ignores JSON key order and encoding whitespace, not differences
  in message text. Do not trim, lowercase, MIME-decode, or otherwise rewrite text
  before identifying the record.
- Do not omit returned source fields through an application projection before
  hashing: two different rows must not become equal merely because detection
  currently ignores a field. No configured `fields` pipe is used on this initial
  polling path. The adapter may discard unneeded values after identification.
- Exclude acquisition metadata such as observation time, request ID, batch
  position, and fields computed by the current query. Such metadata is separate
  from the source row, not silently removed from arbitrary source content.
- The declared view includes the logical source/tenant, field visibility, and
  identity profile. A change to visibility, field selection, canonical encoding,
  or source scope requires an explicit compatibility decision. It does not simply
  create a new namespace and resend history. Credential rotation alone need not
  change the view.
- Replay protection is scoped to the configured input/source view, not globally
  across arbitrary inputs. Shared business-event deduplication is a separate
  processing/detection responsibility.

The digest and its profile identify replay-equivalent input, not an operation,
event, or delivery. A fingerprint has no ordering semantics. `_stream_id` plus
timestamp is neither a substitute fingerprint nor a safe pagination cursor.
Source-hidden fields cannot distinguish records in the authorized view; that
boundary must be declared rather than described as physical-record uniqueness.

[C1 envelopes](identity-and-definition-encoding.md#record-fingerprint) select the
canonical bytes; encoder/API conformance and view-change compatibility remain
[open gates](open-decisions.md#identities-and-source-coverage). The tests must
establish stable results across key order and restart without broadening accepted
equivalence through lossy projection.

## Initial polling behavior

The initial polling path uses an all-or-nothing, bounded read unit:

1. Obtain the committed compatible progress and reserve shared resource capacity.
2. Select one discovery or settlement task and freeze its source view, time range,
   and applicable configuration. Persist acquisition budget state before requests.
3. Keep that unit in bounded memory until response integrity and selection
   completeness have been checked. Do not pass an incomplete prefix to detection.
4. Hand a complete unit to processing. It saves record consequences and proposed
   progress atomically, preserving the common concurrency and deduplication rules.
5. Adopt the new progress only after durable acceptance is known. Release buffers
   and reservations when ownership of the unit ends.

The tradeoff is bounded extra memory and repeated network work after interruption,
in exchange for avoiding a durable raw-record inbox and partially admitted failed
reads. This is the selected polling strategy, not the universal ingestion contract.

## Discovery and late-record settlement

Use two durable coverage frontiers in the source's search-time coordinate:

| Frontier | Meaning |
| --- | --- |
| Discovery | Contiguous range already read completely at least once; new results may be processed immediately |
| Settlement | Contiguous range re-read completely after its supported lateness elapsed; no further ordinary late-record scans are required |

Both begin at an explicitly configured observation start. Settlement never passes
discovery. Absence of an initial start is a configuration error, not permission to
choose an arbitrary historical replay. These frontiers are source progress, not
business timestamps, record IDs, or proof of external delivery.

This observation start is the source context-loading boundary, expressed in the
source search-time coordinate. It is distinct from the business-event notification
cutoff owned by [detection](detection-correlation-and-enrichment.md#observation-and-notification-boundaries).
Reading earlier history can establish context without making its earlier failures
eligible for business notifications. Numeric comparison of source and business
timestamps is not proof of the required coverage relationship.

1. Discovery reads a bounded next interval beginning at its committed frontier.
   A complete accepted read advances discovery and exposes events without waiting
   for the lateness hour.
2. Settlement reads from its own committed frontier, ending no later than both
   discovery and current time minus the supported lateness. That read starts only
   after the whole selected interval is mature. Its new records receive normal
   processing; fingerprints suppress already accepted effects.
3. Settlement progress advances only with durable effects of that final complete
   read. An earlier discovery success cannot stand in for this read.
4. A mature catch-up interval can advance both frontiers in one successful read
   if it is contiguous at both. No second read is required just to repeat already
   mature work.
5. Due settlement has priority over further discovery for the same input. Shared
   scheduling still gives other inputs and lookups bounded turns. No queue entry
   is created for every elapsed poll tick or every minute awaiting maturity.

Intervals are half-open. Child reads can commit a contiguous successful prefix,
never jump past an unaccepted child. A bounded acquisition task retains its frozen
range and budget across retries; source progress is not the maximum record time
seen in a response.

The one-hour contract means a record becomes query-visible no later than one hour
after its source search timestamp; source/collector delay and clock skew must fit
inside that bound. Records outside the bound are not guaranteed. Source records
must remain queryable until settlement and any supported catch-up complete.

This avoids scanning the entire recent hour on every poll, at the cost of delayed
detection for records arriving after discovery. With no backlog, failures, or
capacity pressure, the final check is approximately one lateness interval plus a
window/scheduling delay after source time. This is not a universal latency bound;
retries and paused inputs can delay it further.

Discovery and settlement have independent acquisition budgets. Waiting for a
window to mature does not consume its future settlement retry hour. The wall-clock
budget starts with that task's first acquisition attempt, not with the record's
original timestamp or the earlier discovery task.

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
- Safe operational updates, such as retry state after a failed request, can be
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
automatic read budget exhausted -> paused until explicit resume
incompatible state or unresolvable read limit -> blocked
shutdown -> stopped
```

These describe observable conditions, not a proposed SQL state machine.

After restart, resume committed progress rather than resetting to a window near
the current time. After a crash before durable acceptance, repeat the unit only
within its remaining persisted budgets. If a deadline or attempt/request budget
was exhausted, retain committed progress and pause until explicit resume. A crash
after acceptance recovers its effects and proposed progress from SQLite. Shutdown
does not manufacture successful completion of an interrupted read.

## Late arrivals, retries, and retained state

Discovery and settlement deliberately overlap. An input can have accepted recent
records while older intervals still require settlement. No finite lateness horizon
covers arbitrarily late records or makes missing source history recoverable.

Cleanup preserves replay protection for reads that remain supported, including
inputs paused long enough that a wall-clock TTL would otherwise remove markers.
If storage limits prevent this, losing that guarantee requires an explicit
decision rather than an ordinary resume silently becoming unprotected replay.

Each acquisition task has the agreed one-hour/max-ten-retry policy. Ordinary
successful scheduled reads are not retries; a failed task is not recreated on
each tick to receive a new budget. Transient failure schedules the next attempt
with the selected backoff; permanent failure visibly blocks. Automatic budget
exhaustion pauses the input until explicit resumption, preserving both frontiers.

Apply an additional aggregate cap of 256 network requests and split depth 32 per
original acquisition task. Successful size probes, subdivisions, and retries all
count toward the aggregate request cap. Transient reattempts also consume the
shared retry counter; child tasks do not each receive ten fresh retries. Splitting
inherits the original task's deadline and counters. These additional limits belong
to this approved block contract, alongside the shared retry defaults.

The bounded split plan, current contiguous boundary, and consumed budgets must be
durable or recoverable without replenishment. A scheduler yield or process restart
does not reset any of them. Per-turn limits merely yield execution; exhaustion of
the aggregate deadline/request/depth budget pauses or blocks visibly. There is no
silent skip or new automatic recovery episode after an exhausted one. Explicit
resume creates a new auditable budget at existing progress, without replaying
already accepted effects or silently accepting a changed source view.

No network attempt starts after its deadline; its timeout fits the remaining
budget. A response completed and validated in time may still finish durable
acceptance afterward. Source read budgeting never licenses acknowledging data
before that acceptance.

### Long outages and historical coverage

Resume discovery and settlement at their committed compatible frontiers, not at
the current time. There is no separate arbitrary maximum outage duration after
which progress is automatically discarded. Catch-up remains subject to source
history availability, finite acquisition budgets, fair scheduling, and global
capacity. This is not a guarantee that an arbitrarily old backlog can be recovered.

The original context-loading start and notification cutoff remain fixed across
restart; committed frontiers describe subsequent progress. A long outage does not
replenish exhausted acquisition work, revive terminal candidates, extend context
retention, or refresh existing candidate/delivery deadlines. Newly discovered
eligible events may produce delayed notifications only if their ordinary context,
proof, and processing requirements can still be met.

Confirmed loss of required source history blocks affected polling at committed
progress pending explicit supported recovery. Do not automatically jump over the
lost interval. An operator may accept a gap only through a separately specified
supported operation; this is not an implemented command or implicit permission to
reset progress. Accepted loss remains observable and cannot become complete
historical coverage or evidence for otherwise unproven lifecycle membership.

When historical coverage cannot be verified, retain and report that uncertainty
instead of treating an empty read as proof that no records ever existed. Unknown
history is not automatically confirmed loss; neither condition permits guessed
correlation. Source retention, visibility/clock assumptions, exact recovery
operations, and deployment coverage evidence remain
[open](open-decisions.md#identities-and-source-coverage).

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

The retry defaults are selected in the accepted operating policies. The following
additional initial values are **approved, not benchmarked**. They are configurable
finite limits, not a claim about measured application resource use.

| Setting | Initial value |
| --- | --- |
| Poll interval | 30 seconds, without overlapping polls or accumulated ticks |
| Maximum source interval per request | Five minutes |
| Accepted records per response | 5,000, counted before fingerprint deduplication |
| Wire and decoded response bytes | 8 MiB each, independently bounded |
| Single decoded record | 64 KiB and at most 64 fields |
| Shared ingestion buffer allocation | 64 MiB, including parser and retained record allocations |
| Concurrent source requests | Two globally; at most one read/accept operation per input |
| Scheduler turn | At most eight requests or 60 seconds, whichever comes first |
| Aggregate acquisition task | 256 requests and split depth 32, also bounded by its retry/deadline policy |

The sentinel response described below may contain one additional record solely to
detect overflow; its bytes and parsing allocations still count. Size checks must
precede unbounded allocation. Shared buffer accounting includes parsing overhead
and rejects/defer work before exceeding its reserved budget; it is not a bound on
total Go process RSS. Lookups share the global request/buffer budget fairly.
Storage capacity is a separate mandatory admission constraint defined by the
SQLite/processing block, not an unlimited default.

| Limit | Exhaustion behavior |
| --- | --- |
| Record bytes, field count, field/value size | Explicit failure; no lossy clipping or raw-record quarantine |
| Records and wire/decoded bytes per unit | Incomplete unit; safely narrow/split or block |
| Network timeout and acquisition deadline/retry budget | Retry within the existing task budget or pause visibly when exhausted |
| Per-turn duration/request count | Yield without replenishing aggregate task budgets |
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

Ingestion emits safe error classifications, not destination-specific messages.
Processing-error opt-in and system destinations are routed by the responsible
blocks. Repeated input failures must be coalesced/rate-limited; failure to deliver
an error notice must not create recursive notices. The approved
[routing](routing-and-formatting.md) and [operations](operations-and-observability.md)
contracts define those limits; operational/conformance evidence remains
[open](open-decisions.md#resources-retention-and-operations).

## VictoriaLogs completeness protocol

The [querying documentation](https://docs.victoriametrics.com/victorialogs/querying/)
describes streaming JSONL, unordered results by default, bounded result options,
and partial-response settings. `_stream_id` identifies a stream, not a unique log
record. A successful bounded response is not sufficient evidence of completeness
if the query itself limits, samples, aggregates, or otherwise transforms records.

The initial polling path uses the following deliberately narrow contract:

1. Configure a LogsQL filter expression selecting raw source records. No
   configured pipes, query options, relative/moving time filters, subqueries, or
   generated records are supported in this first contract. Explicit fixed
   `start`/`end` request arguments define the acquisition interval. Portable rules
   perform required extraction from the returned fields/text.
2. Reject unsupported syntax before processing. Validation must be grammar-aware
   and fail closed, not remove suspicious words or split on a pipe character
   inside arbitrary quoted text. This does not select a parser library or permit
   building a general-purpose LogsQL implementation locally. Until subset
   validation is established, unsupported/unverifiable configurations cannot run.
3. Use the raw-record query endpoint and explicitly disable partial responses.
   Configured query options cannot override this or the fixed interval. A
   supported deployment/proxy must preserve the source's error and completion
   semantics rather than hide truncation behind successful HTTP responses.
4. Set the request row limit to accepted capacity plus one. Receive and validate
   the entire response within byte/time/memory limits. Count physical returned
   rows before deduplication. Any extra sentinel row makes the interval incomplete,
   including when the selection contains exactly that many rows. Never accept
   only the first capacity-sized prefix.
5. A response with no sentinel is acceptable only if it also passes HTTP/framing,
   complete JSONL decoding, source-execution error, fixed-range, and resource-limit
   checks under the verified API/version contract. A malformed tail after valid
   rows, timeout, or transport truncation invalidates the entire unaccepted unit.
6. On size/sentinel overflow, subdivide the same fixed half-open interval into
   disjoint smaller intervals and re-read. Preserve the aggregate budget and
   accept only a contiguous completed prefix. Do not paginate by offset or use
   maximum returned timestamp: the source may change and timestamps may tie.
7. If the interval cannot be safely subdivided within representable boundaries or
   the aggregate limits, stop visibly without advancing past it. Dense equal-time
   records can therefore block the input; the design does not promise unbounded
   throughput or silently discard overflow.

The sentinel bounds row volume; it is not independent proof of complete selection.
The public API behavior, rejected query forms, partial-response controls, and
mid-response error signaling must pass version-specific conformance tests before
claiming this adapter's completeness guarantee. An adapter can be refused rather
than relaxing the contract for an unverifiable source/proxy.

The approved filter-only restriction, sentinel protocol, and two-frontier schedule
do not imply support for arbitrary configured LogsQL. Context
lookups require their own approved query bindings and cannot secretly broaden the
polling contract. No source implementation or conformance tests exist yet; the
remaining acceptance evidence is tracked in
[Open decisions](open-decisions.md#identities-and-source-coverage).

## Test criteria

- Complete empty reads differ from failed, truncated, malformed, and partial reads.
- An interrupted response after valid records produces no accepted unit effects
  and no progress advancement under the selected polling strategy.
- Before/after/unknown-commit failures recover from durable state without losing
  obligations or recreating accepted events/delivery assignments.
- Replay, out-of-order records, supported lateness edges, and unsupported lateness
  exercise the declared identity and coverage boundaries.
- Canonical key order/encoding variation does not defeat replay protection;
  original content differences do not collapse through projection. Completely
  identical rows collapse under the accepted policy, including across restart.
- Fingerprint/view changes cannot silently replay history; input equivalence,
  correlation, event, and delivery identities remain distinct.
- Discovery can process immediately; settlement captures late arrivals, including
  those added after discovery, without advancing across unaccepted intervals.
- Maturity waiting does not exhaust future settlement budgets. Mature catch-up,
  different source/business times, and clock/visibility assumptions are exercised.
- Oversized records, splittable windows, equal timestamps, and unresolvable dense
  intervals cannot cause silent loss, unlimited splitting, or false progress.
- Paused-input cleanup preserves the supported replay guarantee or requires an
  explicit, observable decision to change it.
- Capacity, repeated outages, restart cooldowns, and multiple inputs respect
  bounded memory/concurrency and do not create tick backlogs or retry storms.
- Splitting, per-turn yields, recovery, and explicit resume preserve the specified
  aggregate budget and contiguous progress rules. Exhaustion is visible and
  cannot silently start another automatic retry sequence.
- Zero, exactly capacity, and capacity-plus-one result counts exercise sentinel
  handling before deduplication, including duplicate rows and equal timestamps.
- Unsupported query pipes/options/time filters and partial-response overrides
  fail closed; HTTP success with a malformed/error suffix is not accepted.
- A supported-source conformance test covers server-side errors after output has
  begun and the documented limit behavior, not only a locally mocked happy path.
- Source/configuration incompatibility blocks without resetting progress.
- Context-loading start and notification cutoff remain distinct across source and
  business clocks; restart does not move either boundary or reset committed progress.
- Long-outage catch-up respects existing expired/exhausted work and may create
  delayed eligible notifications without promising unavailable context or history.
- Confirmed history loss blocks affected polling; unknown history and complete
  empty reads cannot manufacture coverage. Any supported explicit gap acceptance
  preserves visible loss and cannot bypass lifecycle proof.
- History lookup cannot advance polling progress or trigger unrelated events.
- Dry-run leaves production state unchanged; diagnostics and metric labels do
  not disclose raw records, secrets, or record identifiers.

Tests use synthetic data, HTTP test servers, controllable time, and real temporary
SQLite databases for persistence integration. These are design criteria, not
tests that have been implemented or run.
