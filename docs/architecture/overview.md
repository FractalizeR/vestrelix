# System overview

**Status: approved architectural direction.** Detailed block specifications remain
subject to individual approval. See [Open decisions](open-decisions.md) for the
limits of this baseline.

## Deployment and scope

Vestrelix runs as one Go process with one active instance and a local SQLite
database. Initial integrations are VictoriaLogs and HTTP POST webhooks, with
Pachca as the first intended webhook profile. Supported targets are linux/amd64,
linux/arm64, and darwin/arm64.

Observed services do not call Vestrelix synchronously. In particular, the first
scenario neither changes Postfix configuration nor participates in SMTP delivery.
Existing log storage remains the source of history; SQLite is not a log mirror.
There is no distributed infrastructure, public plugin system, or application
framework in the selected direction.

## Logical blocks and data flow

```text
                       Configuration and process control
                          schedules, limits, lifecycle
                                      |
VictoriaLogs -> Source access -> Extraction -> Detection and enrichment
                               normalization             |
                                                         | normalized event
                                                         v
                                              Routing and formatting
                                                         |
                                                  delivery jobs
                                                         v
                                                   HTTP delivery -> Webhook

Enrichment -> source-specific history lookup -> Source access

---------------------------- SQLite --------------------------------
Read progress, replay protection, correlation context, pending work,
events, destination-specific delivery jobs, and attempt results

Observability, privacy, and resource control span the blocks.
```

These are logical responsibilities, not separate services or mandatory in-memory
queues. The data-flow diagram is not a Go import graph.

| Block | Receives and produces | State responsibility |
| --- | --- | --- |
| Configuration and process control | Configuration and operator requests; validated settings, schedules, and lifecycle actions | Compatibility with persisted work, validation-only behavior, isolated dry-run, and shutdown coordination |
| Source access | Configured reads and context lookups; source records, read outcomes, and proposed progress | Source-specific progress meaning, bounded reads, completeness assessment, and source identity |
| Extraction and normalization | Required source fields or text; usable fields or explicit unsupported/invalid/missing-data outcomes | No separate durable log store; reuse already available fields |
| Detection, correlation, and enrichment | Normalized facts and related context; events, pending enrichment, or explicit unresolved outcomes | Minimal operation context, event identity, enrichment deadlines, and separate event/detection times |
| Routing and formatting | Normalized event; zero or more audience-specific delivery assignments or visible formation failures | Destination selection, field allowlists, and fixed delivery content and destination revision |
| Delivery | Persisted jobs; network attempt outcomes, retry schedules, success, or visible non-delivery | Independent destination queues, concurrency/rate limits, attempt budgets, and recovery of interrupted attempts |
| SQLite state lifecycle | Domain transitions; durable atomic results | Transaction execution, migrations, bounded retention, capacity control, and recovery support |

Domain blocks own the meaning of transitions. SQLite owns their durable
representation, not the business decisions. A processing coordinator connects
those decisions to the required atomic boundaries; see
[Packages and dependencies](packages-and-dependencies.md).

Source queries remain in input configuration. Portable detection logic contains
no LogsQL. Rule configuration cannot supply arbitrary executable code, shell
commands, or executable plugins.

## Four distinct identities

| Identity | Meaning | Insufficient substitute |
| --- | --- | --- |
| Source record | The replay-equivalence identity of a record within an input/source view | Stream ID plus time as a supposedly unique physical-record ID |
| Correlation | A particular observed operation | A Postfix queue ID without originating relay and lifecycle |
| Event | A particular business occurrence under a stable rule | Correlation identity or triggering record identity alone |
| Delivery | A notification of an event to one logical destination | A network attempt identifier |

One operation may produce multiple events. Several records may establish one
event. Each destination has independent delivery state. Network retries reuse the
delivery identity rather than creating new jobs.

For the initial release, a stable fingerprint of the canonical source record is
the accepted replay policy. Completely identical records within the same source
view may collapse, even if they were physically distinct. This deliberate
equivalence is not a uniqueness claim about timestamps, stream IDs, or hashes.
Fingerprint changes require a compatibility decision, not automatic replay.

Restarting or editing a template, rule description, or configuration revision does
not by itself create a new event identity or resend historical notifications.
Canonicalization compatibility and business-occurrence discriminators remain
[open](open-decisions.md#identities-and-source-coverage).

## Agreed operating policies

These choices come from product decisions, not observations about a particular
deployment. The detailed [ingestion contract](ingestion.md) has separate block
approval; the remaining block contracts require their own agreement.

The [extraction and normalization contract](extraction-and-normalization.md) is
also approved. It permits explicit producer fallback chains: equivalent meanings
can use different source keys, invalid-value fallback needs an explicit policy,
and cross-meaning selection is opt-in with retained provenance and accurate
labeling. A header sender does not silently satisfy the first scenario's envelope
sender requirement, and the SMTP null reverse path is a valid present value.

The [detection, correlation, and enrichment contract](detection-correlation-and-enrichment.md)
is approved as well. It defines occurrence identity, proof-gated lifecycle binding,
a three-hour candidate deadline, bounded targeted lookups, and context dependency
retention. Its source-proof gates are requirements, not verified deployment facts.

The [routing and formatting contract](routing-and-formatting.md) is approved,
including frozen audience/field definitions, profile-owned prepared content,
protected local diagnostics, bounded error reporting, and its resource defaults.
JSON belongs to the initial HTTP webhook body, not every output format. Exact
configuration recovery and destination conformance remain evidence/design gates.
The [delivery and HTTP contract](delivery-and-http.md) is also approved, including
attempt ownership, first-start/retry rounds, HTTP classification, server cooldowns,
explicit requeue, and its limits. Transport/profile conformance and state gates
remain outstanding. The [SQLite state lifecycle contract](sqlite-state-lifecycle.md)
is also approved, with automatic terminal expiry/cleanup, a 256 MiB main database
ceiling, and a 384 MiB working-file budget. These are limits, not reserved disk or
measured use. Driver/storage evidence remains outstanding. The next
[configuration and process control block](configuration-and-process-control.md)
is a separate unapproved proposal; its mechanisms and new limits need agreement.

| Policy | Initial choice |
| --- | --- |
| Supported log lateness | One hour; the ingestion contract defines the visibility/clock assumptions |
| Minimal message context | Seven days; expiry anchor, dependencies, and longer-lived operations require the detection/state contract |
| Mail notification time | Receipt by the outbound relay, not the message `Date:` header or earlier submission |
| Automatic retries | Initial attempt plus at most ten retries, subject to a one-hour wall-clock budget |
| Network request timeout | 15 seconds, shortened by the remaining operation budget |
| Exponential retry delay | Start at 15 seconds, double, cap the randomized delay at ten minutes |
| Jitter | Uniform multiplier from 0.9 to 1.1 before applying the ten-minute cap |

The one-hour/approximately-ten-retry direction is approved; the concrete retry
defaults above are selected under the delegated choice of numbers. They remain
configurable. Without jitter the ten delays total 55 minutes 45 seconds. A new
attempt cannot start after the deadline or exceed the remaining budget. Restarts
do not replenish attempts or reset deadlines. Permanent failures do not consume a
full transient retry sequence.

Source-read budget exhaustion pauses the affected input at its committed progress
until explicit resumption. Webhook exhaustion leaves a visibly undelivered job.
Other inputs and destinations remain independently schedulable. Explicit
resumption/requeue budget rules are part of the respective detailed block design.
`Retry-After` cannot be shortened into an early retry: if it cannot be honored
within the applicable bounds and remaining budget, expose the stopped work.

The retry hour is not the supported lifetime of a mail operation, source-history
retention, or the permitted duration of every process outage. Source data must
remain available for catch-up and late-record checks. Seven-day context retention
is not a promise about arbitrary hold, requeue, or externally delayed operations.

Processing failures produce safe structured logs and bounded metrics. A
destination can opt into processing-error messages; a system destination can
receive operational notices. Audience selection, safe fields, admission quotas,
and notification loop boundaries are defined by the approved routing contract;
exact configuration syntax and operational evidence remain outstanding. Metrics
are exposed for external monitoring and alerting; no new alerting adapter is
implied.

## Durable boundaries

### Accepting read results

Read progress advances only together with durable processing consequences:
replay protection, correlation updates, events, pending follow-up work, or explicit
non-applicable/unsupported outcomes. A crash cannot acknowledge source records
while losing their events or necessary further work.

An incomplete or truncated read is not a successful empty read. Progress cannot
skip uncovered portions of a source interval. Earlier independently completed
portions may already be durable, provided replay remains safe.

Completeness of a read concerns the requested selection at that time. It does not
prove that no records with older timestamps will arrive later. Overlap and an
explicit lateness bound address that separate problem.

### Finalizing an event and assigning deliveries

A finalized event is saved with its routing decision and delivery jobs, or with a
durable, visible failure that preserves the unresolved delivery obligation. There
is no unrecorded gap between accepting an event and remembering its delivery work.
Selecting no destinations is an explicit routing outcome.

Network operations are outside SQLite transactions. Concurrent read-modify-write
transitions and ownership of delivery attempts must also be coordinated; atomic
writes alone do not prevent competing workers from overwriting decisions.

### Attempting delivery

A job exists durably before any send. Attempt start is persisted and charged to
its budget before the network operation. The resulting success, error, or next
retry is then saved separately. An interrupted attempt can therefore consume
budget without proving that a request reached the destination.

SQLite and an arbitrary webhook cannot share one transaction. A crash after
sending, or a lost response, leaves an ambiguous outcome. That outcome is retried
within the configured budget, with the same delivery identity and content.

## Delivery and recovery guarantees

- A destination-defined successful response is required before recording success.
- Ambiguous outcomes favor a possible duplicate over silently losing a notification.
  Destination-supported idempotency keys reduce duplicates but cannot be assumed.
- Retry state survives restart: finite timeouts, exponential backoff with jitter,
  a maximum interval, bounded `Retry-After` handling, and finite automatic budgets.
- Permanent failures and exhausted jobs remain visibly undelivered. Inspection,
  explicit retry, expiry, and removal follow a documented retention policy.
- The goal is at-least-once delivery with duplicate-tolerant consumers, not
  unconditional eventual delivery or exactly-once HTTP delivery. A destination
  that never recovers cannot be served by finite automatic retries.
- Incomplete reads are replayed; durable enrichment resumes with its existing
  deadline; interrupted sends recover as ambiguous attempts.
- Commit recovery assumes correct durable SQLite settings and storage behavior.
  It is not protection against losing the database disk.

## First scenario: permanent mail rejection

1. **Observe initial context.** The configured input includes context-bearing
   records, not only rejection records. Preserve minimal envelope sender, subject,
   original time, and sufficient operation-lifecycle evidence when available.
   Bounded history lookup supplements this context. Persisting these facts avoids
   relying exclusively on old log availability for rejection days later.
2. **Recognize a recipient-specific rejection.** Detection requires a matching
   domain, a final delivery failure, and explicit permanent rejection by the remote
   SMTP server. `status=bounced` alone, local errors, deferrals, timeouts, and queue
   expiry without remote rejection do not qualify. Only qualifying rejected
   recipients produce events.
3. **Wait for missing context.** Before read progress advances, missing context
   becomes durable enrichment work. Out-of-order records or history lookup can
   complete it within the allowed wait. Expiry produces a visible unresolved
   outcome, not invented values or a raw-record fallback.
4. **Create permitted messages.** Finalization and routing persist independent
   delivery assignments. Each message contains only envelope sender, rejected
   envelope recipient, decoded subject, and the outbound relay receipt timestamp. It
   excludes body, attachments, other recipients, and raw SMTP diagnostics. JSON
   and destination-specific message values are escaped correctly.
5. **Read the same records again.** Record replay protection prevents repeating
   already accepted record effects where supported by the source identity
   contract. Event and delivery identities independently prevent recreating the
   same business event and destination assignment.
6. **Restart.** Before commit, processing may repeat from committed progress.
   After commit, durable context, enrichment, and jobs survive. A later rejection
   can use preserved original context within the supported observation and
   retention horizon; ambiguous queue-ID reuse never becomes a guessed match.
7. **Lose the webhook response.** If the webhook accepted the POST but its response
   was lost, or the process crashed before saving success, the same job is retried.
   A non-idempotent webhook may display a duplicate. Budget exhaustion records
   non-delivery rather than claiming success.

The source must actually contain the required context. This architecture cannot
recover a subject or lifecycle evidence that was never logged. Observation start,
history availability, missing subject, and domain matching are
listed in [Mail scenario decisions](open-decisions.md#mail-scenario).

## Privacy, capacity, and operations

Persist minimal correlation context rather than raw logs. Record the applicable
rule, configuration, and formatting revisions for admitted work; fix minimal
formatted content and the applicable logical destination revision when admitting
delivery work. Exact compatibility and change policies remain open. Secret
material stays external; references alone must not allow a changed
webhook URL to silently redirect existing jobs. An unavailable destination version
visibly pauses affected work rather than substituting another recipient.

Destination-specific queue/rate/concurrency limits prevent one destination from
monopolizing resources. When its automatic queue reaches capacity, new assignments
to it are recorded as visibly undelivered due to capacity, preserving inspection
and explicit retry while allowing healthy destinations to proceed. Recording these
failures still consumes storage: it is not an infinite fallback queue.

At global storage exhaustion, admission pauses without falsely advancing progress.
Existing deliveries continue only while storage can safely record their changes.
Backlog may outlive source retention; corresponding coverage limitations must be
visible. Pending and failed work never disappears through silent cleanup.

SQLite, memory, query duration/size, processing work, and queues are explicitly
bounded. Retention must preserve replay protection for supported re-reading,
including paused inputs, or require an explicit decision about losing that
guarantee. Concrete limits and recovery policy remain
[open](open-decisions.md#resources-retention-and-operations).

Expose `/metrics` through the standard Prometheus client, including process and Go
runtime collectors and a stable `vestrelix_` application namespace. Labels have
bounded cardinality and exclude event/record IDs and sensitive values. Safe
diagnostics expose polling failures, lag, pending work, attempts, non-delivery,
storage, and cleanup failures without raw records, payloads, credentials, or secret
URLs. `/healthz` and `/readyz` have distinct meanings; a webhook outage does not
trigger a liveness restart loop.

Dry-run neither sends notifications nor changes production state or acknowledges
production delivery jobs. Prevent feedback loops caused by observing Vestrelix's
own notification activity. Graceful shutdown and interrupted-work recovery are
required. Single-active-instance enforcement is local and fail-closed, not a
distributed coordination mechanism.
