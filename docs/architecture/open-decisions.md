# Open decisions

**Status: unresolved.** Approval of the architectural direction does not choose
answers to the questions below. This is the canonical list of open decisions, not
an implementation sequence. Owners are logical blocks, not assigned people.

## Identities and source coverage

| Question or required evidence | Owner |
| --- | --- |
| Reliable record identity for VictoriaLogs, including distinct records with identical text/time and overlapping configured inputs | Source access and ingestion |
| Evidence of complete bounded reads for the supported VictoriaLogs API/version, including partial responses, query operators, equal timestamps, and pagination behavior | VictoriaLogs input |
| Supported lateness, observation start/backfill, outage/catch-up horizon, and source-retention assumptions | Ingestion and processing |
| Stable business-occurrence discriminators distinct from correlation and source records | Detection |
| Replay-protection lifetime and behavior when a paused input still needs old markers | Processing and SQLite state lifecycle |

## Mail scenario

| Question or required evidence | Owner |
| --- | --- |
| Availability of subject, envelope data, and lifecycle evidence without changing Postfix configuration or the SMTP path | Postfix detection profile and source access |
| Unambiguous originating-relay and queue-ID lifecycle identification, including reuse | Postfix detection profile |
| Final timestamp meaning: relay receipt is readily available but not automatically the message `Date:` header or original submission time | Postfix detection profile |
| Recipient domain/subdomain matching and missing/undecodable subject outcomes | Postfix detection profile |
| Maximum supported message lifetime, minimal context contents, retention, and treatment of messages predating observation | Detection and enrichment |
| Enrichment lookup binding, caching, wait/retry bounds, and terminal unresolved outcomes | Detection, processing, and source access |

## Configuration and state compatibility

| Question or required evidence | Owner |
| --- | --- |
| Detailed YAML model, strict parsing limits, field extraction, and bounded condition mechanisms | Configuration and detection |
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
| Concrete timeout/backoff/jitter/`Retry-After` bounds and automatic attempt/time budgets | Delivery |
| Explicit requeue budget/deadline rules and deduplication horizon after retained events/jobs expire | Delivery and processing |

## Resources, retention, and operations

| Question or required evidence | Owner |
| --- | --- |
| Numerical SQLite, memory, read, processing, concurrency, rate, queue, and retention limits | Each resource-owning block |
| Detailed recovery and operator actions after per-destination/global capacity exhaustion; observable expiry/removal of failed work | Delivery, processing, and SQLite state lifecycle |
| Health/readiness criteria, stable metric/alert contract, and diagnostic retention | Operations |
| Local single-active-instance enforcement and supported local-storage assumptions | Process control and SQLite state lifecycle |

The agreed destination-capacity direction is recorded in the
[overview](overview.md#privacy-capacity-and-operations): preserve visible
non-delivery for the affected destination rather than blocking healthy
destinations solely on its automatic queue. Concrete limits and the detailed
recovery/retention contract remain open.
