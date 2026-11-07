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

Approval of an architectural direction is not approval of every block's detailed
contract, algorithm, or numerical limit. A preliminary library selection is not
evidence of operational suitability. Ingestion has separate block approval; its
conformance evidence and explicitly open contracts are still outstanding.

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
