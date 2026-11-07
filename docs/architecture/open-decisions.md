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
| Source/domain evidence for approved replay-marker retirement gates and identity horizons, including paused inputs and later records for old occurrences | Processing and SQLite state lifecycle |

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
| Concrete YAML fields and a complete version-matched offline JSON Schema, examples, supported dialect/editor association, and structural schema/loader agreement tests | Configuration and detection |
| Concrete encodings/compiler evidence and supported transitions under approved frozen-definition/binding compatibility policy; explicit migration/replay paths | Configuration and processing |
| Native evidence for approved offline administration/dry-run isolation; explicit historical replay/reprocessing semantics remain separate | Process control and processing |
| Concrete schemas, supported upgrade paths, driver mechanisms, and evidence for the approved migration/backup/restore policy | SQLite state lifecycle |
| Native/profile validation of approved strict loading, recovered semantic bundles, binding continuity, authority/restore activation, offline admin, dry-run, and limits | Configuration and process control |
| Exact library versions, license/dependency review, resource validation, and native target checks for preliminary selections | Relevant block and development tooling |

## Delivery and HTTP

| Question or required evidence | Owner |
| --- | --- |
| Profile-specific success/error evidence, including Pachca; generic HTTP classification is approved | Delivery and webhook profile |
| Recoverable binding mechanism and evidence for approved target continuity, credential rotation versus recipient changes, and unavailable/revoked references | Configuration, routing, and delivery |
| Conformance of approved no-redirect/one-POST accounting under standard HTTP transport behavior | HTTP delivery |
| Native/resource evidence for approved retry accounting, clock gates, server cooldowns, and first-start versus retry deadlines | Delivery |
| Operational evidence for approved bounded attempt diagnostics and response privacy; any richer response capture needs a new decision | Delivery and operations |
| State protection/retention for approved explicit requeue budgets and operation IDs, and deduplication after retained jobs expire | Delivery, processing, and SQLite state lifecycle |
| Transport conformance for one POST exchange per charged attempt and profile-specific success/idempotency evidence, including Pachca | HTTP delivery and webhook profile |

## Resources, retention, and operations

| Question or required evidence | Owner |
| --- | --- |
| Resource validation of approved ingestion limits; remaining SQLite, processing, rate, queue, and retention limits | Each resource-owning block |
| Resource/format validation for approved extraction limits, single-observation boundaries, and explicit fallback behavior | Extraction and normalization |
| Resource/source validation of approved lifecycle gates, candidate merge/terminal policy, domain matching, wait/lookup/context limits, and retention dependencies | Detection, correlation, and enrichment |
| Resource/profile validation of approved routing snapshots, field policies, profile-owned formats, protected diagnostics, error quotas, and loop boundaries | Routing and formatting |
| Resource/native validation of approved delivery queue, rate, concurrency, and diagnostic limits | Delivery and HTTP |
| Native/resource validation of approved SQLite durability, writer/read limits, retention, marker retirement, reduced storage reserves, maintenance, and restore hold | SQLite state lifecycle |
| Detailed recovery and operator actions after per-destination/global capacity exhaustion; observable expiry/removal of failed work | Delivery, processing, and SQLite state lifecycle |
| Health/readiness criteria, stable metric/alert contract, and diagnostic retention | Operations |
| Detailed local inspection, auxiliary snapshot expiry/capacity accounting, and recoverable formatter definitions | Operations, routing, and SQLite state lifecycle |
| Operational evidence for approved error/system scope, safe fields, bounded repetition, and internal/external loop prevention | Routing, delivery, and operations |
| Local single-active-instance enforcement and supported local-storage assumptions | Process control and SQLite state lifecycle |

The agreed destination-capacity direction is recorded in the
[overview](overview.md#privacy-capacity-and-operations): preserve visible
non-delivery for the affected destination rather than blocking healthy
destinations solely on its automatic queue. Delivery queue limits and explicit
requeue and reduced global state capacity/retention are approved. Ordinary expiry
and cleanup are automatic; fresh retry budgets and exceptional recovery remain
explicit operator actions. Driver/storage and retirement evidence remain open.

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
mechanisms. The [delivery/HTTP block](delivery-and-http.md) is also approved,
including its retry/first-start accounting, HTTP policy, cooldowns, requeue, limits,
and diagnostic privacy. Transport/profile evidence remains outstanding. The
[SQLite state lifecycle contract](sqlite-state-lifecycle.md) is approved, including
automatic expiry/cleanup and reduced storage limits. Driver/storage validation,
concrete migration paths, and source/domain retirement evidence remain open. The
[configuration and process control contract](configuration-and-process-control.md)
is also approved, with a required user/agent-facing YAML configuration schema.
Concrete YAML fields and the complete schema artifact do not exist yet; approval
does not establish implementation, native/profile conformance, or schema/loader
agreement. Operations/health/metrics remain to be designed and approved.
