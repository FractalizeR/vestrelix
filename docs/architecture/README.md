# Architecture

Vestrelix is in architectural design. No application is implemented, and these
documents are not an implementation plan.

[Functional scope](../../FEATURES.md) defines the product requirements. The
architecture describes the agreed direction for satisfying them; it does not
silently override requirements or close unresolved decisions.

## Document status

| Document | Status | Scope |
| --- | --- | --- |
| [System overview](overview.md) | Approved architectural direction | Logical blocks, state ownership, transaction boundaries, guarantees, and the first scenario |
| [Packages and dependencies](packages-and-dependencies.md) | Approved direction; technology selections are preliminary | Package responsibilities, dependency boundaries, input extensibility, and library choices |
| [Open decisions](open-decisions.md) | Unresolved | Questions that still need an explicit decision or evidence |
| [Ingestion](ingestion.md) | Approved block contract; implementation and conformance pending | Input contract, polling, completeness, recovery, limits, and test criteria |
| [Extraction and normalization](extraction-and-normalization.md) | Approved block contract; not implemented | Typed facts, explicit fallback, field quality, deterministic profiles, subject/time handling, limits, and test criteria |
| [Detection, correlation, and enrichment](detection-correlation-and-enrichment.md) | Approved block contract; implementation and source proof pending | Lifecycle proof, occurrence identity, bounded context/waiting/lookups, finalization, retention, and test criteria |
| [Routing and formatting](routing-and-formatting.md) | Approved block contract; implementation and destination conformance pending | Audience/field policies, profile-owned messages, protected diagnostics, error/system destinations, and test criteria |
| [Delivery and HTTP](delivery-and-http.md) | Approved block contract; implementation and transport/profile conformance pending | Attempt ownership, HTTP outcomes, retry rounds, restart, explicit requeue, limits, and test criteria |
| [SQLite state lifecycle](sqlite-state-lifecycle.md) | Approved block contract; implementation and driver/storage conformance pending | Durability, concurrency, retention, reduced capacity defaults, automatic expiry/cleanup, migrations, backup/restore, and test criteria |
| [Configuration and process control](configuration-and-process-control.md) | Approved block contract; implementation, concrete YAML/schema, and conformance pending | Strict settings, required user/agent schema, recovered definitions/bindings, process ownership, activation, isolated dry-run, and test criteria |
| [Operations and observability](operations-and-observability.md) | Approved block contract; implementation and native/deployment conformance pending | Liveness/readiness, safe logs, bounded metrics, external alert signals, serving limits, and test criteria |

Approval of an architectural direction is not approval of every block's detailed
contract, algorithm, or numerical limit. A preliminary library selection is not
evidence of operational suitability. Ingestion, extraction, detection, routing,
delivery, SQLite state, configuration/process control, and operations have separate
block approval; conformance evidence and explicitly open contracts remain outstanding.

The [agreed operating policies](overview.md#agreed-operating-policies) record
fingerprint equivalence, time/context bounds, retry defaults, and the direction of
error reporting. The ingestion contract separately approves its read/scheduling
limits and test criteria, not the results of unimplemented source-protocol tests.

## Specification boundaries

Detailed block specifications are reviewed and approved individually. They cover
contracts, state, algorithms, failure handling, resource limits, security, and test
criteria. Approval of one block does not approve the next block or authorize
implementation.

All logical blocks listed above now have architectural approval. This closes the
block-by-block architecture discussion, not implementation readiness. Concrete
contracts and required evidence remain tracked in [Open decisions](open-decisions.md).
In particular, exact YAML fields and the required complete user/agent schema have
not been produced; there is no supported configuration artifact or application yet.

Open questions have one canonical description in [Open decisions](open-decisions.md).
Topic documents describe the corresponding limits of their guarantees and link
there rather than choosing missing answers implicitly.

The package tree describes intended responsibilities, not an instruction to create
empty packages. Go interfaces, SQL schemas, dependency version pins, and an
implementation sequence are outside the current baseline.
