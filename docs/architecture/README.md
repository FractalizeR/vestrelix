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
| [Delivery and HTTP](delivery-and-http.md) | Review-ready proposal; not approved | Attempt ownership, HTTP outcomes, retry rounds, restart, explicit requeue, limits, and test criteria |

Approval of an architectural direction is not approval of every block's detailed
contract, algorithm, or numerical limit. A preliminary library selection is not
evidence of operational suitability. Ingestion, extraction, detection, and routing
have separate block approval; source evidence and explicitly open contracts remain
outstanding.

The [agreed operating policies](overview.md#agreed-operating-policies) record
fingerprint equivalence, time/context bounds, retry defaults, and the direction of
error reporting. The ingestion contract separately approves its read/scheduling
limits and test criteria, not the results of unimplemented source-protocol tests.

## Specification boundaries

Detailed block specifications are reviewed and approved individually. They cover
contracts, state, algorithms, failure handling, resource limits, security, and test
criteria. Approval of one block does not approve the next block or authorize
implementation.

Open questions have one canonical description in [Open decisions](open-decisions.md).
Topic documents describe the corresponding limits of their guarantees and link
there rather than choosing missing answers implicitly.

The package tree describes intended responsibilities, not an instruction to create
empty packages. Go interfaces, SQL schemas, dependency version pins, and an
implementation sequence are outside the current baseline.
