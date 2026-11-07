# Functional scope

This document records the agreed product direction, not implemented capabilities
or a step-by-step implementation plan. The repository currently contains only
bootstrap and publication-security tooling.

## Purpose

Vestrelix detects individual events in logs, obtains their relevant context,
persists notification jobs, and delivers selected information to configured
destinations. It targets cases such as an individual delivery rejection or a
background job that has exhausted its retries, rather than a threshold-based
infrastructure alarm.

The deployment model is one Go process, one active instance, and SQLite for local
state. No separate database server is required. Existing log storage remains the
source of history; Vestrelix is not another log database.

Notification delivery must not become a dependency of the systems being observed.
The first use case must not require a synchronous hook, filter, or network call
inside the mail-delivery path.

## Processing model

Logical responsibilities, not separate services:

1. **Input adapters** retrieve records and handle source-specific read progress.
2. **Extraction and normalization** produce fields from structured records or text.
3. **Detection and enrichment** identify events and obtain related information.
4. **Persistent state** records progress, events, and independent delivery jobs.
5. **Routing and formatting** select destinations and permitted message fields.
6. **Delivery adapters** perform network operations with bounded concurrency.

A source record is not necessarily an event. Several records may describe one
operation, while one operation may produce multiple distinct events. Record
identity, correlation identity, event identity, and destination-specific delivery
identity must be distinct concepts.

## Initial release requirements

### Inputs and configuration

- Poll VictoriaLogs with configurable schedules and bounded query windows.
- Keep each LogsQL query in its input configuration. The VictoriaLogs driver
  executes queries; source-independent detection rules do not embed LogsQL.
- Support multiple configured inputs, rules, and destinations within one process.
- Extract fields only when needed; reuse fields already returned by the source.
- Support explicit field-producer fallback chains while preserving meaning and
  provenance. Cross-meaning fallback requires opt-in and accurate labeling;
  invalid values cannot silently disappear through fallback. A valid SMTP null
  reverse path is not missing sender data.
- Persist read progress and resume after restart.
- Handle duplicate and late-arriving records through overlapping windows and
  deduplication. Define the supported lateness bound explicitly; arbitrary delays
  cannot be covered by a finite lookback window.
- Initially support log lateness up to one hour. For record replay protection,
  accept collapsing completely identical records within one source view using a
  stable content fingerprint; this is not a claim of physical-record uniqueness.
- Bound request duration, response size, and records processed per query.
- Distinguish a successful empty result from a failed, truncated, or incomplete
  query. Do not advance progress as though incomplete data were fully processed.
- Validate configuration before processing and provide a validation-only command.
- Provide a version-matched JSON Schema for YAML configuration, with descriptions
  and synthetic examples for users, editors, and agents. Support local/offline
  structural validation and test agreement with the strict loader; keep semantic,
  state-compatibility, and source/profile checks explicit and separate.
- Provide a dry-run mode that evaluates rules without delivering notifications or
  acknowledging production delivery jobs.

### Detection and enrichment

- Configure field extraction, event conditions, and correlation/deduplication keys.
- Give rules stable identifiers, independent of their human-readable descriptions.
- Obtain related fields from source history or persisted state as appropriate.
- Keep source-specific enrichment queries separate from portable event logic.
- Tolerate related records arriving out of order with a bounded enrichment wait.
- Define explicit outcomes for missing fields, unsupported records, and expired
  enrichment attempts; do not silently invent values or discard failures.
- Log processing failures safely, allow destinations to opt into processing-error
  notifications, and support destinations designated for system notifications.
  Keep error reporting bounded and prevent recursive notification failures.
- Preserve event time separately from detection time.
- Produce a normalized event before formatting a destination-specific message.
- Do not execute arbitrary code, shell commands, or executable plugins supplied
  through rule configuration.

### SQLite state

- Persist input progress, detected events, pending enrichment, delivery jobs, and
  attempt results.
- Make progress advancement consistent with durable processing results so a crash
  cannot acknowledge source records while losing their events or follow-up work.
- Store delivery jobs before attempting network delivery.
- Deduplicate replayed records and notifications across restarts.
- Do not copy all source logs into SQLite. Prefer bounded history lookups and
  retain only the state necessary for processing and delivery.
- Bound retained data and define cleanup, capacity-exhaustion, and recovery
  behavior explicitly. Pending or failed work must not disappear silently.

### Routing and HTTP delivery

- Support more than one destination for an event, with independent delivery state,
  queues, retry policies, and rate/concurrency limits.
- Make HTTP POST the first delivery adapter. Pachca is the first intended webhook
  profile; support configurable JSON message formatting rather than coupling
  event detection to its payload format.
- Route events by configured conditions and select an explicit allowlist of
  fields for each destination. Different audiences may receive different details.
- Use stable delivery identifiers and destination-supported idempotency keys
  where available; do not assume every webhook supports them.
- Mark delivery successful only after a destination-defined successful response.
- Retry ambiguous outcomes, including a lost response or a crash after sending.
  Duplicates are preferable to losing notifications.
- Persist retry state across restarts. Use exponential backoff with jitter and a
  maximum interval, finite network timeouts, and appropriate handling of HTTP 429
  and `Retry-After` within configured bounds.
- Distinguish transient transport failures from permanent request/configuration
  failures, and expose both without retry storms.
- Bound automatic retry work by a configured time and/or attempt budget. Exhausted
  jobs become visibly undelivered and remain available for inspection and explicit
  retry under a documented retention policy.
- Use an initial automatic retry policy of approximately ten retries within one
  hour for source reads and webhook delivery. Persist budgets across restarts;
  source-read exhaustion pauses the affected input without advancing progress.
  Selected defaults are recorded in the architecture, not implemented behavior.
- Provide an explicit operation to requeue undelivered jobs.
- A failing destination must not block other destinations or the observed service.

The delivery goal is **at least once**, with duplicate-tolerant consumers. Finite
automatic retries cannot guarantee eventual delivery to a destination that never
recovers. An exhausted job is not successful: retain and expose that failure rather
than claiming unconditional at-least-once or exactly-once delivery. Any later
expiry or removal is an explicit, observable retention decision.

### Standard monitoring and operations

- Expose `/metrics` using Prometheus/OpenMetrics-compatible exposition and the
  standard Go client, including process and Go runtime collectors.
- Use a stable application metric namespace, `vestrelix_`. Distinguish instances
  and environments through scrape labels, not different metric prefixes.
- Report source polling failures, last successful polling time, processing lag,
  detected events, delivery attempts and latency, pending-job counts and age, and
  undelivered/expired jobs. Make storage and cleanup failures observable.
- Keep metric label cardinality bounded. Never label metrics with message
  subjects, recipient addresses, event IDs, or other unbounded/sensitive values.
- Expose `/healthz` and `/readyz`, with distinct liveness/readiness semantics.
  External destination outages must not trigger pointless liveness restart loops.
- Emit structured diagnostic logs without credentials, raw payloads, or sensitive
  event fields by default.
- Support graceful shutdown and recovery after an interrupted operation.
- Make SQLite, queue, memory, and processing limits operationally explicit.

### Security and privacy

- Keep real credentials and deployment-specific configuration outside the public
  repository; use synthetic fixtures and reserved example domains.
- Do not expose secret webhook URLs, authentication headers, or private source
  data in diagnostic output, metrics, or error messages.
- Treat SQLite as potentially sensitive storage: restrict access and apply the
  documented retention policy.
- Send only explicitly allowed fields. Do not forward an entire source record as
  an accidental fallback when enrichment or templating fails.
- Escape values correctly when formatting JSON and destination messages.
- Prevent notification loops, including delivery failures for the service's own
  email notifications when that adapter is introduced.

## First acceptance scenario: permanent mail rejection

The first scenario observes Postfix delivery logs through VictoriaLogs. It does
not change Postfix configuration or participate in SMTP processing.

An event requires all of the following:

- The recipient domain matches a configured allowlist.
- Delivery has finally failed for that particular recipient.
- The logs contain an explicit permanent rejection from the remote SMTP server.

`status=bounced` alone is insufficient: local failures can also cause a bounce.
Temporary deferrals, network timeouts, local configuration/DNS errors, and queue
expiry without a confirmed remote rejection are outside this notification rule.
SMTP acceptance also cannot establish inbox placement or detect silent discards.

For a message with multiple recipients, create events only for rejected recipients
whose domains match the allowlist. Correlation must account for the originating
relay and the queue-ID lifecycle, including potential ID reuse.

The notification contains only the SMTP envelope sender, the rejected SMTP
recipient, the decoded subject, and the timestamp of receipt by the outbound
relay. Do not include the body, attachments, other recipients, or raw SMTP
diagnostics.

Envelope addresses need not equal the `From:`/`To:` headers. The notification time
means receipt by the outbound relay, not the message's `Date:` header or an earlier
submission elsewhere. A rejection days later must still be correlated with the
original message, including across Vestrelix restarts. Initially retain minimal
message context for seven days. Longer-lived operations need an explicit policy;
context expiry cannot silently remove pending processing or delivery obligations.

## Extension points, not initial-release commitments

- **Additional inputs:** files with rotation handling, HTTP ingestion, and queues.
- **Additional outputs:** SMTP email, other webhook profiles, and Alertmanager.
  Alertmanager requires a defined active/resolved lifecycle; do not model every
  one-off event as an infrastructure alert automatically.
- **Scheduled digests:** group already detected events by period, destination, or
  operation instead of sending every event individually.
- **Additional event rules:** final external-integration rejection, exhausted
  background-job retries, failed document processing/signing, and selected
  successful completion or recovery events.
- **Missing-completion detection:** identify operations that started but did not
  finish within a deadline. This needs timers, persistent expectations, lateness
  handling, and safeguards against treating a logging outage as a business failure.

Keep detection, routing, and delivery independent so these extensions do not
require rewriting existing event rules. Do not build all adapters in advance.

## Non-goals

- A new log database or a distributed stream-processing platform.
- A replacement for infrastructure monitoring, Alertmanager, or uptime probes.
- A custom general-purpose query language or arbitrary-code rule engine.
- A web UI, distributed execution, or multiple active instances in the first release.
- Exactly-once delivery to arbitrary HTTP endpoints.
- Continuous mirroring of all source records into SQLite.

## Decisions to resolve during design

- Concrete YAML fields/schema and supported operators for the approved bounded
  condition/extraction mechanisms.
- Canonical fingerprint encoding and adapter-specific completeness/lateness
  evidence under the approved source-read contract.
- Concrete enrichment bindings, recoverable definitions, and source-proof evidence
  under the approved wait/lookup/expiry contract.
- Native/resource evidence for approved capacity, retention, retry, and exhaustion
  policies, including page/WAL amplification and safe identity retirement.
- Evidence for approved dry-run isolation; explicit history replay/reprocessing
  behavior remains a separate contract.
- Concrete rule/configuration encodings, supported compatibility transitions,
  SQLite schemas, and migration paths under the approved lifecycle policy.
- Native health/readiness/metric behavior and concrete externally evaluated alert
  rules under the approved operations contract; deployment thresholds need tuning.
- Internationalized address/source-format support, context/history availability,
  and evidence for the required queue-ID lifecycle proof in the mail scenario.

Changing a template or restarting the process must not silently resend historical
events. History replay and manual retries are explicit operations, not incidental
effects of a configuration reload.
