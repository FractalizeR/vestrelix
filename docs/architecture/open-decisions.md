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
| Stable business-occurrence discriminators distinct from correlation and source records | Detection |
| Replay-protection lifetime and behavior when a paused input still needs old markers | Processing and SQLite state lifecycle |

## Mail scenario

| Question or required evidence | Owner |
| --- | --- |
| Availability of subject, envelope data, and lifecycle evidence without changing Postfix configuration or the SMTP path | Postfix detection profile and source access |
| Unambiguous originating-relay and queue-ID lifecycle identification, including reuse | Postfix detection profile |
| Recipient domain/subdomain matching, supported subject charsets/folding, malformed/control/truncation outcomes, and terminal-error timing | Postfix detection profile |
| Seven-day context expiry anchor, dependencies of pending work, minimal contents, longer-lived operations, and messages predating observation | Detection and enrichment |
| Enrichment lookup binding, caching, wait/retry bounds, and terminal unresolved outcomes | Detection, processing, and source access |

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
| Binding old jobs to destination versions, credential rotation versus recipient changes, and unavailable/revoked references | Configuration, routing, and delivery |
| Redirect policy and relation between durable attempts and physical sends, including standard HTTP transport retries | HTTP delivery |
| Detailed retry accounting and error classification under the selected defaults, including `Retry-After` handling and queue wait versus attempt deadline | Delivery |
| Explicit requeue budget/deadline rules and deduplication horizon after retained events/jobs expire | Delivery and processing |

## Resources, retention, and operations

| Question or required evidence | Owner |
| --- | --- |
| Resource validation of approved ingestion limits; remaining SQLite, processing, rate, queue, and retention limits | Each resource-owning block |
| Resource/format validation for approved extraction limits, single-observation boundaries, and explicit fallback behavior | Extraction and normalization |
| Approval of proposed lifecycle finalization gates, candidate merge/terminal policy, domain matching, wait/lookup/context limits, and retention dependencies | Detection, correlation, and enrichment |
| Detailed recovery and operator actions after per-destination/global capacity exhaustion; observable expiry/removal of failed work | Delivery, processing, and SQLite state lifecycle |
| Health/readiness criteria, stable metric/alert contract, and diagnostic retention | Operations |
| Destination processing-error opt-in versus system-notification scope, safe fields, bounded repetition, and recursion prevention | Routing, delivery, and operations |
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
