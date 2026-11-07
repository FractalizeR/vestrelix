# Open decisions

**Status: unresolved.** Approval of the architectural direction does not choose
answers to the questions below. This is the canonical list of open decisions, not
an implementation sequence. Owners are logical blocks, not assigned people.

## Identities and source coverage

| Question or required evidence | Owner |
| --- | --- |
| Canonical fingerprint encoding and source-view compatibility, including field visibility, overlapping inputs, and changes to the full identity representation | Source access and ingestion |
| Acceptance evidence for the approved bounded-read protocol and supported VictoriaLogs API/version, including query-subset validation, mid-response errors, partial responses, and equal timestamps | VictoriaLogs input |
| Observation-start/backfill policy, outage/catch-up horizon, and deployment evidence for the approved visibility/clock and source-retention assumptions | Ingestion and processing |
| Canonical encoding/compatibility of approved business-occurrence keys, distinct from correlation and source records | Detection |
| Replay-protection lifetime and behavior when a paused input still needs old markers | Processing and SQLite state lifecycle |

## Mail scenario

| Question or required evidence | Owner |
| --- | --- |
| Availability of subject, envelope data, and lifecycle evidence without changing Postfix configuration or the SMTP path | Postfix detection profile and source access |
| Unambiguous originating-relay and queue-ID lifecycle identification, including reuse | Postfix detection profile |
| Supported internationalized addresses, source subject charsets/folding, and format evidence for malformed/control/truncation outcomes | Postfix detection profile |
| State/resource validation of approved receipt-anchored context expiry and candidate pinning; longer-lived operations and pre-observation history evidence | Detection and enrichment |
| Concrete enrichment lookup bindings and source evidence within approved wait/request budgets | Detection, processing, and source access |

## Configuration and state compatibility

| Question or required evidence | Owner |
| --- | --- |
| Detailed YAML model, strict parsing limits, syntax/compatibility for approved extraction precedence and fallback semantics, stable references, and bounded conditions | Configuration and detection |
| Compatibility and transition policies for recorded rule/input/configuration/format revisions, including explicit migration/replay choices | Configuration and processing |
| Exact dry-run isolation and explicit historical replay/reprocessing semantics | Process control and processing |
| SQLite schema migrations, supported upgrade paths, backups, and interrupted/failed upgrade recovery | SQLite state lifecycle |
| Exact library versions, license/dependency review, resource validation, and native target checks for preliminary selections | Relevant block and development tooling |

## Delivery and HTTP

| Question or required evidence | Owner |
| --- | --- |
| Destination success criteria and permanent/transient error classification | Delivery and webhook profile |
| Recoverable binding mechanism and evidence for approved target continuity, credential rotation versus recipient changes, and unavailable/revoked references | Configuration, routing, and delivery |
| Redirect policy and relation between durable attempts and physical sends, including standard HTTP transport retries | HTTP delivery |
| Detailed retry accounting and error classification under the selected defaults, including `Retry-After` handling and queue wait versus attempt deadline | Delivery |
| Bounded retained attempt/response diagnostics, including receiver-echoed sensitive data and limits of wire/reproduction evidence | Delivery and operations |
| Explicit requeue budget/deadline rules and deduplication horizon after retained events/jobs expire | Delivery and processing |
| Approval of the delivery/HTTP proposal, including first-start deadlines, attempt ownership, HTTP restrictions, cooldowns, manual rounds, queue/rate limits, and diagnostic limits | Delivery and HTTP |
| Transport conformance for one POST exchange per charged attempt and profile-specific success/idempotency evidence, including Pachca | HTTP delivery and webhook profile |

## Resources, retention, and operations

| Question or required evidence | Owner |
| --- | --- |
| Resource validation of approved ingestion limits; remaining SQLite, processing, rate, queue, and retention limits | Each resource-owning block |
| Resource/format validation for approved extraction limits, single-observation boundaries, and explicit fallback behavior | Extraction and normalization |
| Resource/source validation of approved lifecycle gates, candidate merge/terminal policy, domain matching, wait/lookup/context limits, and retention dependencies | Detection, correlation, and enrichment |
| Resource/profile validation of approved routing snapshots, field policies, profile-owned formats, protected diagnostics, error quotas, and loop boundaries | Routing and formatting |
| Detailed recovery and operator actions after per-destination/global capacity exhaustion; observable expiry/removal of failed work | Delivery, processing, and SQLite state lifecycle |
| Health/readiness criteria, stable metric/alert contract, and diagnostic retention | Operations |
| Detailed local inspection, auxiliary snapshot expiry/capacity accounting, and recoverable formatter definitions | Operations, routing, and SQLite state lifecycle |
| Operational evidence for approved error/system scope, safe fields, bounded repetition, and internal/external loop prevention | Routing, delivery, and operations |
| Local single-active-instance enforcement and supported local-storage assumptions | Process control and SQLite state lifecycle |

The agreed destination-capacity direction is recorded in the
[overview](overview.md#privacy-capacity-and-operations): preserve visible
non-delivery for the affected destination rather than blocking healthy
destinations solely on its automatic queue. Concrete limits and the detailed
recovery/retention contract remain open.

The [agreed operating policies](overview.md#agreed-operating-policies) close the
choices of record-equivalence semantics, one-hour lateness, seven-day minimal
context, relay receipt time, the initial retry direction/defaults, and support for
error/system destinations. The [ingestion block](ingestion.md) has separate
approval for its polling protocol, fingerprint policy, lifecycle, limits, and test
criteria. That approval does not close the unanswered contracts or establish the
acceptance evidence above.

The [extraction block](extraction-and-normalization.md) is approved with explicit
producer fallbacks and semantic provenance. Approval does not select every source
format/charset or close the remaining configuration and compatibility questions.

The [detection block](detection-correlation-and-enrichment.md) is approved,
including its proof requirements, three-hour candidate deadline, lookup limits,
domain policy, and retention dependencies. The exact supported source-generation
proof still needs evidence; approval does not establish it.

The [routing block](routing-and-formatting.md) is approved, including profile-owned
formats, protected diagnostics, its limits, and independent error/system policies.
It does not establish destination behavior or choose recoverable configuration
mechanisms. The [delivery/HTTP proposal](delivery-and-http.md) remains unapproved;
its detailed answers to the delivery questions above require separate agreement.
