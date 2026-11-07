# Operations and observability

**Status: review-ready proposal; not approved. Not an implementation baseline.**

This block proposes health/readiness meaning, safe logs, bounded metrics, and
signals for external alerting. Upstream approval does not approve the new probe,
telemetry, or alert defaults here. No handlers, collectors, alert-rule files,
application code, SQL schemas, or implementation sequence exist by this proposal.

## Responsibility and independent failure signals

Operations consumes typed domain outcomes and bounded state snapshots. It does
not query source history, classify business events, assign recipients, retry
deliveries, or change retained work because a probe failed. Logging/scraping is
not part of the durable acknowledgment transaction and cannot authorize progress.

Keep three questions separate:

| Signal | Meaning | Not a claim of |
| --- | --- | --- |
| Liveness | The local process-control loop continues to run | Every worker, source, destination, or disk is healthy |
| Readiness | Authoritative local processing is activated and has fresh evidence that required state transitions can be recorded safely | All external dependencies are reachable or every notification was delivered |
| Scoped degradation | A particular input, rule, assignment, destination, or resource needs attention | The process should be restarted |

A webhook outage, rejected request, source outage, terminal unresolved candidate,
or exhausted delivery job does not itself fail liveness. Even all external paths
being unavailable can coexist with local readiness and critical degradation.
Global storage admission failure can make readiness false while liveness stays
true and already admitted work drains where its own safe reservations permit.
These signals observe domain decisions; they do not override their safety gates.

## Probes and background evidence

Propose fixed GET endpoints with small constant text responses and HTTP 200/503:

- `/healthz`: 200 after the process-control loop is initialized and its independent
  heartbeat is fresh; 503 when it is observed stalled. Use a five-second heartbeat
  and a 60-second stale threshold initially. External I/O results do not set it.
- `/readyz`: 200 only when authority/restore activation, compatible local setup,
  admission gates, process-control freshness, and writable-state evidence permit
  normal processing. Startup, draining, unresolved authority, global admission
  pressure, or failed/unknown/stale writable evidence give 503.
- `/metrics`: Prometheus/OpenMetrics exposition, not a health assertion. It can
  remain available during disk failure, exposing the failure and stale snapshots.

Probe handlers read cached typed state and monotonic age only. They perform no
SQLite transactions, source requests, webhook tests, migration, cleanup, or
requeue. Responses contain no configured identities, failure excerpts, database
paths, configuration, or payloads. A readiness failure is not a restart command.
A liveness failure can indicate an internal stall, but host starvation or a long
runtime pause can also delay heartbeat; no probe proves all scheduling is healthy.

Keep three independent evidence streams: process heartbeat, writable-state
confirmation, and retained-work inventory. A blocked writer must not block the
heartbeat or probe handlers. Inventory staleness has its own signal; it is not
by itself proof that the local processing core cannot work.

Propose inventory refresh every 15 seconds through bounded owner aggregates and
short state reads, not full-store scans from each scrape. Reconstruct retained
gauges after restart before marking them known. Shared state deadlines, read
limits, and capacity reservations still apply. Missing inventory is unknown,
not an empty queue; failed refresh retains the last values with an increasing age.

For writable confirmation, recent successful domain commits can supply evidence.
When otherwise idle, propose at most one low-priority control-state probe every
30 seconds. It makes a real bounded change and commit in a constant-size control
record, without growing history or changing source/job budgets. An empty
transaction or unchanged-value optimization is not a write test. Use ordinary
writer ownership/reservations and resolve unknown commit status before retry.
Never start a replacement while the old probe is physically unfinished.

Failed/unknown writable evidence immediately prevents ready status; evidence
older than 60 seconds is stale. A successful probe cannot clear an independent
authority, capacity, clock, or restore gate. The observation is evidence of a past
commit, not a guarantee that the next disk write will succeed. Do not reserve an
unlimited emergency write path for monitoring.

Startup can fail before an HTTP listener exists; safe stderr and the external
monitor's missing-target signal cover that case. Static validation, offline
maintenance, inspection, and dry-run do not promise daemon endpoints. Planned
downtime can use explicit finite external maintenance windows; this introduces
no internal silence/acknowledgment workflow.

## Endpoint exposure and bounded serving

Propose a required normal-run listener on `127.0.0.1:9818` by default. Failure to
bind prevents worker startup rather than silently running unmonitored. Explicit
remote exposure requires a trusted network or protected reverse proxy and an
operator-reviewed exposure setting in the eventual configuration/schema.
Operational counts and configured names can be sensitive even without payloads.
There is no new built-in identity service or assumption that these endpoints are
safe on the public Internet.

Expose only the three fixed GET paths. Do not add pprof, expvar, configuration,
debug, payload, admin, or metrics-triggered mutation endpoints. Reject unsupported
methods/paths without reflecting input. Disable arbitrary access-log fields:
request URI/query, headers, user agent, and client address are not automatic safe
diagnostics. Any endpoint telemetry uses fixed endpoint names and closed results.

Additional initial serving limits are **proposed, not approved or benchmarked**:

| Setting | Initial proposal |
| --- | --- |
| Concurrent full metric renders | Two |
| Complete encoded scrape response | 2 MiB |
| Combined operations snapshot/render/log buffer allocation | 8 MiB, not total Go heap/RSS |
| HTTP connections | 16 |
| Request headers / read-header timeout | 8 KiB / two seconds |
| Write / idle timeout | Five seconds / ten seconds |

Use the standard Prometheus client with bounded collectors. Render permits and
reserved buffers remain held until nested collectors and retained allocations
actually finish, even if the caller timed out. A hung collector cannot create an
unbounded succession of replacement goroutines. Known renderer saturation or
failure returns a failed scrape, not a partial successful exposition. Complete
bounded encoding must succeed before a success response is committed; never
silently truncate families to fit the byte limit.

Cached health handlers do not wait behind metric-render permits. This isolates
them from rendering load, not from arbitrary listener connection saturation,
network failure, or host exhaustion. Common connection/time limits and trusted
deployment access reduce that risk; absolute probe availability is not promised.

## Metric semantics and bounded cardinality

Use the required standard `client_golang` process and Go collectors. Application
families have a stable `vestrelix_` prefix; environment/instance identity comes
from external scrape labels, not a different application prefix per deployment.
Propose the initial families below; names/types/closed enums become a versioned
exposition contract only after approval and implementation conformance.

Per-ID families cover current configured inputs, rules, and destinations only.
Retired work remains visible in separate aggregate families rather than creating
labels for every historical ID/revision. Never use record/event/job/diagnostic
IDs, revision hashes, addresses, subjects, URLs, queries, arbitrary errors, or
unbounded server response fields as labels. Do not combine input, rule, and
destination IDs into an unrestricted cross-product.

Metric enum vocabularies are fixed by their owning contract. Unknown internal
classes map to a closed `unknown` class where allowed, never to the original
string. Unsupported registrations are validation errors, not silently discarded
families. Precompute the supported configuration's maximum application series,
including histogram buckets, sum, and count. Propose at most 5,000 application
series; native collector output also counts toward exposition/memory limits.
The series cap alone does not prove the byte/allocation caps: both need measured
and worst-case native conformance before the configuration is supported.

Counters below are process-lifetime telemetry and reset on restart. Observe
durable domain consequences only after their commit is known; a crash can lose
an in-memory increment. Counters are not an exact durable audit or proof of a
physical send. Retained gauges come from durable owner state, not replay of those
counters. Snapshot-known and age signals qualify gauges; omit uninitialized
inventory values instead of presenting unknown as zero. Known-empty ages are zero.

All names in the following tables have the `vestrelix_` prefix. Labels shown as
input/rule/destination mean the corresponding configured logical ID, not raw data.

### Core, source acquisition, and coverage

| Family | Type / labels | Meaning |
| --- | --- | --- |
| `ready` | Gauge | Current cached readiness, 0/1 |
| `control_heartbeat_age_seconds` | Gauge | Monotonic age of independent process-control heartbeat |
| `state_writable` | Gauge | 1 only with confirmed current writable evidence; failure/unknown is not success |
| `snapshot_known`, `snapshot_age_seconds` | Gauges / kind | Evidence availability/age; kind is control, writable, or inventory |
| `input_enabled` | Gauge / input | Current configured work enabled; operator suspension differs from runtime exhaustion |
| `input_state` | One-hot gauge / input, state | Ready, reading, accepting, retry-wait, budget-paused, operator-paused, capacity-wait, or blocked |
| `source_requests_total` | Counter / input, phase, outcome | Adapter-observed exchange outcomes; phase discovery/settlement/lookup, outcome complete/incomplete/transport-error/protocol-error/canceled |
| `ingestion_records_total` | Counter / input, disposition | Newly accepted or duplicate records from durably accepted complete units; no failed-read prefix counts as accepted |
| `input_last_accept_timestamp_seconds`, `input_last_accept_known` | Gauges / input, phase | Last durably accepted discovery/settlement unit, including a successful empty unit; known flag distinguishes no success yet |
| `input_work_due`, `input_due_age_seconds` | Gauges / input, phase | Whether ordinary discovery/settlement work is currently expected, and age of its continuing unmet due work |
| `input_coverage_lag_seconds`, `input_coverage_known` | Gauges / input, phase | Compatible discovery/settlement backlog, not opaque cursor values |
| `input_history_gap`, `input_history_unverified` | Gauges / input | Independently retained evidence of missing or unverifiable supported history |

Acquisition completeness is distinct from durable acceptance. Request outcome
counters alone cannot establish progress. Ordinary discovery lag is the positive
age behind its committed frontier in the source search-time coordinate. Settlement
excess lag subtracts the approved one-hour lateness from frontier age; normal
maturity waiting is not an hour of processing failure. Both depend on compatible
observation start/frontiers and the declared source/clock contract.

The due-work signal stays false while no settlement interval is mature. Lookup
is demand-driven, so it does not get a periodic polling-success alert. For due
work that has never succeeded, due age still increases; do not hide permanent
startup failure behind a false last-success-known flag. Frontiers can be current
despite a known gap or unverifiable earlier history. Lag/empty reads do not prove
historical completeness, and raw progress coordinates are not emitted in logs.

### Processing, routing, and delivery

| Family | Type / labels | Meaning |
| --- | --- | --- |
| `processing_outcomes_total` | Counter / rule, outcome | Committed finalized/not-applicable/unresolved-terminal transitions |
| `candidates`, `candidate_oldest_age_seconds` | Gauges / rule, state for count only | Unfinished candidates in proof-wait/context-wait/ready/paused state, and oldest unfinished age |
| `processing_unresolved` | Gauge / rule, reason | Retained terminal unresolved outcomes: missing-context, identity-unproven, conflict, deadline, lookup-budget, capacity, or incompatible-definition |
| `routing_unresolved` | Gauge / rule, reason | Retained audience-missing/audience-conflict/definition-incompatible outcomes without inventing a destination |
| `assignment_failures` | Gauge / destination, reason | Retained formation/capacity failures, including failures before a sendable delivery job exists |
| `delivery_jobs` | Gauge / destination, state | Retained ready/in-flight/retry-wait/paused/undelivered/successful/expired dispositions |
| `delivery_attempt_starts_total` | Counter / destination | Durably charged attempt starts, including those interrupted before any network bytes |
| `delivery_attempt_results_total` | Counter / destination, outcome | Committed success/transient/permanent/ambiguous/canceled results |
| `delivery_terminal_total` | Counter / destination, reason | New terminal dispositions, not repeated observation of the same stopped round/assignment |
| `delivery_first_start_oldest_age_seconds` | Gauge / destination | Oldest live round still awaiting its first charged attempt, not an already-started retry round |
| `destination_cooldown_remaining_seconds` | Gauge / destination | Retained representable server not-before delay; an unrepresentable blocked delay remains a paused condition, not zero permission to send |
| `notice_admissions_total`, `notice_suppressed_total` | Counters / destination, closed reason | Error-notice routing admission/suppression, distinct from network retry accounting |
| `retired_work` | Gauge / kind, state | Aggregate retained input-work/candidate/unresolved/routing-failure/delivery dispositions for IDs absent from current configuration |
| `retired_outcomes_total` | Counter / component, outcome | Aggregate observed transitions for retired scopes, without historical ID labels |

Live automatic queue occupancy includes only ready, in-flight, retry-wait, and
paused delivery states, as approved. Terminal retained metadata is not an occupied
queue slot. Assignment-capacity failures and undelivered deliveries can describe
the same obligation; do not sum them as a count of unique incidents. Persistent
failure alerts use gauges, including retired aggregates, not process counters.
New-failure counters describe transitions; manual rounds can legitimately create
another terminal transition without becoming another business event.

Expiry is observable non-delivery/retention, never proof of successful sending.
The disappearance of a retained failure after its approved expiry means the
alert condition ended, not that the message was subsequently delivered. Normal
expiry/cleanup needs no operator acknowledgment to stop a reminder condition.

### Resources and telemetry itself

| Family | Type / labels | Meaning |
| --- | --- | --- |
| `retained_objects`, `retention_pins`, `oldest_pin_age_seconds` | Gauges / kind | Counts and pinned ages for context/candidate/replay-marker/event-identity/delivery-identity/manual-result/definition/diagnostic-snapshot state |
| `expired_content_total` | Counter / kind | Committed explicit content-retirement transitions |
| `diagnostic_snapshots_unavailable_total` | Counter / reason | Oversize, auxiliary-budget, unavailable-dependency, or persistence failure; no content |
| `storage_file_bytes` | Gauge / area | Main, working-family, WAL, backup, maintenance, or dry-run allocated files; overlapping areas are not additive |
| `storage_budget_bytes` | Gauge / area | Corresponding configured main/working/backup/maintenance/dry-run budgets, not a WAL hard-cap promise |
| `storage_used_page_bytes`, `storage_usable_page_bytes` | Gauges | Used versus usable main-page admission budget, accounting for free-page reuse and approved completion headroom |
| `filesystem_available_bytes` | Gauge | Available bytes on the relevant state volume, without path/device labels |
| `wal_admission_threshold_bytes` | Gauge | Approved WAL admission-stop threshold, not an enforced absolute file-size ceiling |
| `admission_blocked` | Gauge / component, limit | Current owner-reported admission gates; component/limit pairs are a closed finite registry |
| `cleanup_failures_total` | Counter / class | Bounded safe busy/full/I/O/integrity/unknown classes |
| `operation_duration_seconds` | Histogram / operation | Source-exchange, state-commit, or delivery-exchange duration, not end-to-end event latency or receiver display time |
| `log_records_omitted_total` | Counter / reason | Coalesced/rate-limited/queue-full/sink-failed telemetry events |
| `metrics_render_failures_total` | Counter / reason | Saturation/timeout/size/collector/unknown failures, without error text |

Propose histogram bucket boundaries of 0.005, 0.025, 0.1, 0.5, 1, 5, 15, and 60
seconds, plus the mandatory infinite bucket. Separate actual file allocation from
logical content and usable capacity: a main file that stays large after deletion
can have reusable pages. Missing volume/inventory evidence is unknown and stale,
not fabricated free space. Monitoring cannot remove pins to lower these gauges.

## Safe bounded structured logs

Propose JSON structured logs through `log/slog` to stdout, INFO by default. Use
fixed event codes, component/stage, safe configured identifiers, closed classes,
counts, and optionally the approved opaque diagnostic reference. That reference
is not a capability and never a metric label. No raw exception serialization,
records, subjects, addresses, target URLs, headers, payloads, arbitrary server
messages, query text, or configuration dump, including at DEBUG. DEBUG can add
typed execution metadata only; content requires the approved protected offline
inspection surface.

Log lifecycle changes and bounded failure summaries, not one record per observed
source line, successful send, retry tick, or cleanup row. Propose a single sink
writer, a 128-record/256 KiB queue, and at most 2 KiB per encoded record. Use a
five-record/second, burst-20 global limit plus at most one repeated-summary record
per code/component/configured scope in 30 seconds. Aggregate counts rather than
queue a delayed message per occurrence or introduce a digest feature.

Bound coalescing to 1,024 keys and 512 KiB; keys exclude event/job/record IDs and
source values. At overflow use a bounded component/code summary and loss counts.
Coalescing, rate limiting, queue loss, and sink failure have distinct omission
accounting. A blocked sink does not block business workers or spawn replacement
writers: retain physical ownership until the old write stops or the process exits.
Timeout does not grant another writer over the same stuck sink.

Never log recursively about a failed log write or emit a notification per omitted
record. Durable domain failure cases/audit protection do not depend on log delivery.
If both sink and scraping are unavailable, immediate visibility of losses cannot
be guaranteed. External log collection/retention is deployment-owned; no SQLite
log mirror, new telemetry framework, file-rotation service, or tracing pipeline is
introduced. Fatal errors before telemetry initialization get safe best-effort
stderr, not a guarantee that arbitrary terminal I/O will return promptly.

## External alerts, not automatic business actions

Expose metrics for external Prometheus-compatible rule evaluation and alert
delivery. No new Alertmanager output adapter or internal threshold-based alarm
engine is introduced. Error/system notices remain governed by the already approved
audience, quota, and loop policies, and cannot replace independent monitoring.

The following initial thresholds are **proposed**, not measured workload SLOs:

| Signal | Suggested external condition |
| --- | --- |
| Process/scrape absent | Failed scrape for two minutes; expected-target inventory also detects targets missing from discovery |
| Local processing unsafe | Not ready, failed/unknown writable state, or global admission blocked for one minute: critical |
| Inventory/evidence stale or unknown | Evidence unknown for 60 seconds or older than 60 seconds: warning; unknown/stale for five minutes: critical; this alert must not require the missing/stale data to be fresh |
| Expected source polling absent | Enabled, due discovery/settlement work unmet for five minutes: warning, including no success ever; not lookup or legitimate maturity waiting |
| Input budget exhausted/blocked | Current enabled input unexpectedly budget-paused/blocked: critical; intentional operator suspension is distinct |
| Coverage behind | Discovery lag or settlement excess lag over ten minutes for five minutes: warning; known gap/unverified history remains a separate warning |
| Candidate near expiry | Oldest unfinished candidate over two hours 30 minutes: warning, leaving part of its three-hour budget |
| Unresolved/routing/delivery failure retained | Positive processing-unresolved, routing-unresolved, assignment-failure, or undelivered gauge for one minute: critical, including retired aggregates |
| First attempt delayed | Live first-start wait over 15 minutes: warning; do not apply this to the normal age of a started one-hour retry round |
| State capacity pressure | Used usable-page or working-file budget over 75%: warning; actual admission stop, WAL pressure unable to drain for one minute, or volume below its required floor: critical |
| Telemetry/diagnostics incomplete | Log loss, unavailable diagnostic snapshots, or notice suppression: warning alongside the underlying failure signal |

Domain inventory conditions require the relevant known/fresh snapshot, with
separate unknown/stale alerts to avoid invented zero or permanently hidden missing
data. Current `ready = 0`, failed/unknown writable evidence, and unknown/stale
evidence alerts are exceptions: never filter them by requiring the same evidence
to be healthy/known/fresh. Core readiness/evidence flags remain exposed while
inventory is unknown. Thus a fresh heartbeat with unknown inventory and unknown
writable evidence gives readiness 503 and the one-minute critical condition;
it does not wait for the five-minute stale-inventory critical threshold.
Newly observed failures can also use transition counters, but retained
gauges are required after counter reset or crash. Scope persistent alerts by
bounded configured component/input/rule/destination, not individual mail/job IDs.
External alert grouping/reminders do not alter job identity, notice quotas, or
delivery budgets.

Expected catch-up and planned offline maintenance may need finite external alert
windows; do not silently claim history loss or suppress real lag indefinitely.
Retention expiry can resolve an alert without delivery recovery; alert text must
not claim otherwise. Alert handling does not automatically requeue, erase work,
reset cursors/budgets, weaken limits, or restart the process for an external outage.
The monitor itself needs independent operational coverage: Vestrelix cannot prove
its own scraper/alert system is alive. Concrete rule files, messages, and threshold
tests are required before claiming an operational alert package exists.

## Proposed test criteria and evidence gates

- Synthetic HTTP tests and controllable time distinguish startup, core stall,
  source/output outage, global storage failure, restore hold, and draining. Cached
  probes cannot issue business/network/state mutations or expose sensitive data.
- Real temporary SQLite tests cover confirmed control writes, no-op detection,
  uncertain commits, writer saturation, stale inventory, startup unknown gauges,
  and independent heartbeat/writable/inventory evidence without overlapping probes.
- Empty accepted reads count as progress; failed prefixes do not. Due-phase/no-
  success-ever, settlement maturity, normal lateness, catch-up, known gaps, and
  unverified history produce distinct observations.
- Metric fixtures verify names/types/enums, current/retired scope accounting,
  histogram series, worst-case configured cardinality, native collector output,
  byte/allocation bounds, and absence of values/IDs prohibited as labels.
- Renderer abuse, collector stalls, cancellations, partial failures, and slow
  clients cannot cause unbounded work or a partial successful scrape. Health
  isolation is tested for renderer load without claiming immunity to connection
  saturation or host/network failure.
- Blocked log sinks, coalescing/queue pressure, DEBUG, arbitrary HTTP errors,
  receiver-echoed content, and malicious request paths preserve privacy, bounded
  physical writers, and non-recursive loss accounting.
- Alert fixtures cover unknown/stale evidence, no successful polling, pre-delivery
  formation failure, retired failures, budget/capacity thresholds, process counter
  resets, and automatic expiry/cleanup without operator acknowledgment or claims
  of successful delivery. External outages never request a liveness restart.
- A fresh heartbeat with unknown inventory and unknown writable evidence remains
  unready and reaches its one-minute critical alert without being hidden by a
  known/fresh inventory filter.

These are proposed criteria, not implemented endpoints, collectors, log delivery,
or verified alerts. Exact YAML fields and the required user/agent schema remain
pending; this block does not create a placeholder schema or authorize application
implementation. Native resource/serving behavior and deployment alert tuning
remain explicit evidence gates.
