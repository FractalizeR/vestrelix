# Packages and dependencies

**Status: approved architectural direction and preliminary technology choices.**
This document does not approve detailed block contracts, create package
placeholders, pin dependency versions, or establish implementation readiness.

## Package map

Use one module, `github.com/FractalizeR/vestrelix`, and internal application
packages. Go packages and import paths provide the relevant namespace boundaries;
there is no public SDK or general-purpose plugin API.

```text
cmd/
└── vestrelix/                  CLI entry point

internal/
├── process/                    Component assembly and process lifecycle
├── configuration/              Configuration loading and validation
├── ingestion/                  Common source-record admission boundary
│   └── victorialogs/            VictoriaLogs reads and history lookup
├── detection/                  Extraction, rules, correlation, enrichment
│   └── postfix/                Postfix formats and operation semantics
├── routing/                    Audience selection, allowlists, formatting
├── delivery/                   Jobs, attempts, budgets, retry scheduling
│   └── webhook/                HTTP exchange and response classification
├── processing/                 Coordination of durable processing
├── sqlitestate/                Concrete SQLite state persistence
│   └── migrations/             Embedded migration resources
└── operations/                 Metrics and health/readiness endpoints
```

The tree maps responsibilities, not a requirement to create empty packages.
Migration resources are not necessarily a Go package. Further subdivision follows
the detailed design of each subject, not anticipated adapters or class roles.

### Assembly and processing

`process` is the explicit composition root: it selects concrete adapters, connects
components, and manages startup/shutdown. It is not the business pipeline.

`processing` coordinates accepting read results, resolving enrichment work, and
finalizing events together with routing/delivery consequences. It does not
interpret Postfix text, execute HTTP requests, contain SQL, or duplicate delivery
retry policy. It owns coordination requirements for concurrent shared-context
updates; the durable transition contract must prevent lost updates.

### Business and adapter boundaries

- `ingestion` owns common source-record and progress-handoff concepts.
  `ingestion/victorialogs` owns LogsQL, source identity and progress interpretation,
  windowing, and source-specific completeness assessment.
- `detection` owns event/correlation concepts, extraction, rules, and enrichment
  decisions. `detection/postfix` understands Postfix lifecycle and rejection
  evidence, not VictoriaLogs queries or destination payloads.
  The approved [extraction and normalization contract](extraction-and-normalization.md) covers
  its record-to-facts boundary; event/correlation contracts remain separate.
  [Detection, correlation, and enrichment](detection-correlation-and-enrichment.md)
  is the approved contract for turning those facts into events; source proof and
  explicitly open contracts remain outstanding.
- `routing` owns recipient/audience selection, field allowlists, and message
  formation from normalized events, retaining applicable formatting revisions.
  The approved [routing and formatting contract](routing-and-formatting.md)
  defines profile-owned message formats, protected diagnostics, and
  the error/system notification boundary. JSON is the initial webhook body format,
  not a required representation for all output protocols.
- `delivery` owns job identity, attempt state, bounded retry scheduling, and
  destination isolation. `delivery/webhook` performs network operations and
  classifies responses rather than running a separate hidden retry loop.
  The [delivery and HTTP contract](delivery-and-http.md) is approved; its
  transport settings and destination predicates still require conformance evidence.
- Pachca initially remains a webhook configuration profile. A separate package
  needs actual profile-specific behavior, not merely a destination name.
- `operations` exposes bounded operational summaries, not arbitrary business
  event dumps. Instrumentation can remain near its subject without forcing core
  blocks to depend on the endpoints package.
  The [operations and observability contract](operations-and-observability.md) is
  approved; it separates local readiness/liveness from external degradation.
  Native serving/collector behavior and concrete deployment alert rules remain
  unverified/unimplemented.

### Persistence

`sqlitestate` is the single concrete state backend. It contains SQL, durable commit
execution, migrations, and cleanup execution, not business policy. The required
atomic acceptance boundaries are described in the [overview](overview.md#durable-boundaries).
Independently committing one repository per domain cannot replace them.

The [SQLite state lifecycle contract](sqlite-state-lifecycle.md) is approved,
including reduced storage defaults and automatic expiry/cleanup. Native
driver/storage validation and concrete schemas/migration paths remain outstanding.
The [configuration and process control contract](configuration-and-process-control.md)
is approved; it addresses recovered definitions, bindings, activation, and a
required user/agent schema. Concrete YAML/schema, gated operator transitions,
and native evidence remain outstanding; no schema artifact or runtime support is
implemented yet.

Consumer blocks describe the persistence behavior they need; the backend
implements it using subject-owned concepts. Core blocks do not import the backend
or receive SQL access. Safe operational status updates may be committed separately
provided they neither acknowledge records nor advance source progress.

### Import rules

- Shared parent packages do not import their concrete adapter children.
- Concrete adapters can depend on the relevant common concepts. Assembly selects
  implementations explicitly, without global `init` registration or runtime plugins.
- Subject types remain with their owner: records in `ingestion`, events and
  correlation in `detection`, jobs and attempts in `delivery`.
- Narrow interfaces belong at actual consumer boundaries, not around every type.
- There are no catch-all `common`, `utils`, `models`, `services`, `repositories`,
  or `adapters` directories.

## Extensible inputs without a source framework

Separate acquiring records from accepting their durable processing consequences.
The common boundary handles source-neutral records, explicit read outcomes, and
progress handoff. It does not make VictoriaLogs' `Read(start, end)` model the
required contract of every future source.

Each input has a stable configured identity, type, common safety constraints, and
typed settings for that type. VictoriaLogs-specific settings include connection
details, credential references, LogsQL, and polling/window behavior. Unknown types
or settings for the wrong type fail validation. Adapter settings do not flow
through portable event logic as an untyped configuration bag.

The adapter owns the meaning and version of source progress. Durable processing
controls whether it may be committed with the consequences of accepted records.
An adapter cannot independently acknowledge records before that commit.

Record replay protection initially uses a stable canonical content fingerprint
with the accepted possibility of collapsing fully identical records within one
source view. This does not merge correlation, event, or delivery identities. A
changed field projection or fingerprint profile is a compatibility change, not an
incidental configuration revision that resends history.

Transport and log format are independent: Postfix logic can consume suitable
records from another input without learning that input's transport. Adding an
input changes its adapter, typed configuration, and assembly; it does not require
rewriting routing or delivery merely because the transport changed.

History lookup is a separate source capability, not a mandatory universal
`Search(query)` facility. Detection describes needed context and correlation
values; `processing` binds that need to a configured input lookup and parameter
mapping. The adapter applies source-specific query syntax safely. Results return
through the required extraction to the requester. Portable rules contain no
LogsQL, and the VictoriaLogs adapter does not decide Postfix business outcomes.

No hypothetical file/queue/HTTP-ingestion adapters are created now. Future inputs
need not support polling, replay, history lookup, or equal completeness guarantees.
The [ingestion specification](ingestion.md) is an approved block contract. Its
source conformance evidence and explicitly open compatibility contracts remain
outstanding; approval is not authorization to implement it.

## Framework decision

No application framework is selected. Use explicit component construction and
the standard library for HTTP, cancellation, structured logs, JSON, regular
expressions, initial CLI handling, and tests.

Gin/Echo, a DI container, an ORM, an event bus, and a workflow framework do not
provide the required correlation and durability guarantees. Those guarantees are
application responsibilities; SQL engines, encoders, metrics exposition, and
configuration parsers are not reimplemented locally.

| Mechanism | Standard package |
| --- | --- |
| HTTP clients and operational endpoints | `net/http` |
| Cancellation, deadlines, shutdown | `context`, `os/signal` |
| Structured logs | `log/slog` |
| SQLite access boundary | `database/sql` plus a driver |
| JSON and regular expressions | `encoding/json`, `regexp` |
| Optional subject hint decoding | `mime.WordDecoder` for bounded best-effort display; additional charset support only when useful and reviewed, without a custom strict validator or closed alias table |
| Initial CLI | `flag` |
| Tests | `testing`, `net/http/httptest`, fuzzing |

Using `net/http` alone does not establish one physical send per durable attempt:
redirects and some transport retries need an explicit policy. See
[HTTP decisions](open-decisions.md#delivery-and-http).

## Dependency direction

The following selections were approved at the architectural level. Except for
the product requirement to use the standard Prometheus client, they are
preliminary technology choices, not installed dependencies or claims of validated
resource use. No versions are pinned by this document.

| Purpose | Selection | Qualification |
| --- | --- | --- |
| Metrics | `github.com/prometheus/client_golang` | Required by functional scope |
| SQLite driver | `modernc.org/sqlite` | Preferred for CGO-free application builds; validate resources and recovery on all targets |
| Migrations | `github.com/pressly/goose/v3` | Embedded library use; not the all-driver CLI or a substitute for upgrade/recovery policy |
| Rate limiting | `golang.org/x/time/rate` | In-process mechanism, not durable retry scheduling |
| Configuration | YAML with `go.yaml.in/yaml/v4` as parser candidate | Approved strict/bounded loading policy; concrete YAML/schema and parser conformance remain pending |
| Canonical identity/definition envelopes | Core Deterministic CBOR with `github.com/fxamacker/cbor/v2` as encoder candidate | Selected C1 value/envelope contract; version/license/resource/decoder review and concrete definition AST bodies remain pending |

### SQLite tradeoff

`modernc.org/sqlite` documents support for the three target platforms without
CGO. This simplifies application builds, not necessarily resource consumption.
CPU cost, transitive dependencies, memory use, binary size, and bounded connection
pools require validation against the expected workload. Its documented
`modernc.org/libc` version coupling must be respected when pinning dependencies.

`github.com/mattn/go-sqlite3` is the CGO alternative using native C SQLite. It
requires a C toolchain for building the application. Selecting a CGO-free driver
does not remove the existing C compiler requirement for race tests.

### Configuration and deferred dependencies

YAML is selected for nested configuration and multiline LogsQL. Do not add another
configuration format or Viper as an incidental dependency. Unknown fields and
duplicate keys must be rejected, and parser errors must not expose secret-bearing
source excerpts. The [configuration contract](configuration-and-process-control.md)
is approved; exact YAML/schema, definition AST bodies, gated operator transitions,
and conformance remain
[open gates](open-decisions.md#configuration-and-state-compatibility).

No expression library is selected. Start from bounded declarative conditions and
existing extraction mechanisms; a richer language needs an agreed expression and
resource contract. No independent HTTP-retry wrapper is selected: automatic
delivery retries belong to persisted attempt accounting. An interval schedule
does not require a cron library. `golang.org/x/sync/errgroup`, comparison helpers,
and extra charset support are conditional on actual needs, not baseline imports.

## Upstream references

These sources inform the choices; reading them is not a dependency security audit
or a native compatibility test.

- [Prometheus Go client](https://github.com/prometheus/client_golang)
- [modernc SQLite](https://pkg.go.dev/modernc.org/sqlite)
- [CGO SQLite alternative](https://github.com/mattn/go-sqlite3)
- [Goose](https://github.com/pressly/goose)
- [Go rate limiter](https://pkg.go.dev/golang.org/x/time/rate)
- [YAML organization Go implementation](https://github.com/yaml/go-yaml)
- [HTTP client behavior](https://pkg.go.dev/net/http#Client.Do)
- [HTTP transport behavior](https://pkg.go.dev/net/http#Transport)
