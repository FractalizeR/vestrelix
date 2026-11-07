# Operator and compatibility contract

**Status: selected technical specification under delegated architectural design.
Not implemented or native/state/profile-conformance-verified.**

This fixes the initial command surface and compatibility decisions that do not
change approved product guarantees. It does not implement commands, generic
historical replay, schema migrations, or a permissive configuration schema.
Unknown or explicitly gated transitions remain unavailable, not operator force
options. The owning block contracts retain all resource, authority, and privacy
requirements.

## Command selection and authority

Use `vestrelix [--control-root PATH] COMMAND ...`. `--control-root` explicitly
selects an installation root for commands that use one; it never selects a bare
SQLite file. No current-directory state discovery or environment-driven overlay
is supported. Roots in command examples are operator-selected private locations,
not repository artifacts. The concrete YAML model must not introduce a competing
implicit state-root selector.

`help` and `version` need neither state nor credentials. Version output identifies
the binary and supported configuration, interpreter, and state formats, not the
host environment or installed secret references. Every command rejects unknown
flags and positional arguments. There are no aliases that imply force, live admin,
or hidden network probes.

| Command | Required selection and effects |
| --- | --- |
| `validate --config FILE` | Read the selected YAML and perform strict static structural/semantic checks only; no control-root acquisition, production state open, secret resolution, network, or migration |
| `init --config FILE --confirm-new-installation` | Exclusive root ownership; initialize private key/control state and empty supported SQLite only; refuse an existing installation; explicit recovery of an incomplete initialization is not normal run |
| `run --config FILE` | Exclusive lifetime root ownership; validate authority, state, retained definitions, bindings and activation before worker I/O; never implicitly initialize/migrate/restore |
| `dry-run --config FILE --from UTC --until UTC` | Explicit half-open source interval; root ownership and isolated managed workspace under the existing ten-minute/64-request budget; no production SQLite, identity-key read, target-secret resolution, or sender |
| `inspect KIND [--id ID] [--limit N] [--cursor TOKEN]` | Exclusive offline ownership; protected read-only bounded retained-state view; no workers, source queries, sends, migrations, or secret resolution |
| `inspect-content KIND --id ID --acknowledge-sensitive-output` | Explicit protected local content view of one retained object, not a wire capture, data export service, or retry operation |
| `input resume --config FILE --input ID --expected-revision REV` | Admit a new finite acquisition episode only for retained budget-paused input work after continuity/capacity gates; no direct source read |
| `delivery requeue --config FILE --delivery ID --expected-revision REV --operation-id ID --policy ID --acknowledge-possible-duplicate` | Admit one new round for a retained formed undelivered job under the already approved operation-protection contract; no POST |
| `state backup` | Explicit offline consistent image, verified private publication and bounded managed inventory; no source/delivery I/O or identity-key export |
| `state migrate --to FORMAT` | Only an implemented registered forward transactional path with verified backup/history; no automatic downgrade, schema rebuild, or mark-applied override |
| `state compact` | Explicit offline compaction with verified backup, reserved workspace and finite maintenance deadline; never manual WAL deletion |

All root-using commands, including dry-run and inspection, share the same
canonical ownership/alias checks and exclusive lock. A busy root causes refusal,
not a request that the running daemon stop. Static validation does not inspect
production state to predict compatibility. Protected filesystem access remains
the access boundary; command names or diagnostic references are not capabilities.

The table describes selected syntax, not existing executables. No command takes
literal credentials, webhook URLs, arbitrary SQL/LogsQL, or executable expressions
as flags. Required external bindings are resolved only by modes that need them;
inspection/backup cannot resolve secrets simply to enrich their output.

## Frozen work and activation classification

Compare the proposed validated semantic graph with retained definitions and
state under exclusive ownership. Static success is not activation success.
Changes apply as follows, without an implicit historical processing pass:

| Change | Initial supported decision |
| --- | --- |
| Display label/nonsemantic description | No event, delivery, budget, or progress identity change |
| Poll schedule or process-local concurrency/rate cap | Apply validated settings after controlled restart; do not recreate due tasks, replenish budgets, or bypass durable destination pacing/cooldowns |
| A timeout, attempt/deadline policy, or work limit used by an admitted task/round | Preserve its retained policy and consumed work; a new setting applies to new admissions or an explicitly admitted manual round, not retroactively to the old round |
| Global memory/storage/connection/queue safety limit | Enforce at activation/execution; refuse or visibly pause incompatible dependent work instead of evicting it or exceeding the new bound |
| Route/template/field policy or bounded rule predicate preserving the supported occurrence/proof meaning | New origin admissions use the new closure; existing candidates/events/assignments retain their original closure and identity protection |
| A newly configured destination or error/system opt-in | New eligible origins only; do not replay retained history or reopen suppressed/terminal cases |
| Disabled/removed input or rule | Stop new reads/admissions as appropriate; retain compatible context, progress and obligations; missing dependencies pause old work without extending deadlines |
| Disabled/removed destination or revoked binding | Block sending even for old jobs; retain selected obligations and ordinary expiry; do not redirect or reinterpret as no destination |
| External reference moved/renamed, actual resolved values unchanged | Permit only after retained revision/tag and immutable resolver continuity pass; pathname/name equality is not evidence |
| Generic source/target credential or opaque URL values changed | Block dependent old work and affected source progress until a verified profile-specific transition exists; no authentication-only assumption |
| Source scope/view/query meaning, extraction/proof interpretation, input ownership, occurrence key, logical identity, envelope format, or interpreter meaning changed incompatibly | No generic automatic transition; reject affected activation/admission or visibly pause known dependent work |
| Observation/context-loading start or notification cutoff changed | No implicit backfill, skip, replay, or reassignment; an explicitly supported boundary transition is required and remains a gate |

Safe reduction is not "delete until the count fits". Count pinned work, retired
scopes, revisions, physically unfinished attempts, reservations, and cleanup needs.
New global bounds cannot be exceeded merely because a job was previously admitted;
old admission is not permission to discard it either. If both obligations cannot
be honored, refuse the incompatible activation or pause dependent execution. A
limit edit/restart never changes the original expiry anchor or restores consumed
work. Increases beyond a validated resource/profile range remain unsupported even
when the numeric value is syntactically finite.

Tightening a field policy does not revoke frozen old authorizations by itself.
Operators who need to stop old disclosures explicitly disable/revoke the relevant
destination binding/work. Current revocation wins over retained definitions.
Unknown global authority/state formats stop normal activation; an unsupported old
definition can pause only its known dependent work, as the configuration contract
already permits. There is no hot reload, SIGHUP activation, rename-to-reset rule,
or generic state-mapping language.

## Input resume and delivery requeue are different

Input resume checks the retained input's monotonically increasing control
revision, compatible source view/binding, paused acquisition state, and capacity.
The successful transition changes that revision and records the new episode while
preserving committed frontiers and durable split/acceptance state. A repeated old
request is stale and cannot obtain another episode. Revisions never wrap or reset
when an input disappears from current configuration; retained identity protection
still applies. Do not silently fetch the latest revision and retry a mutation.

An uncertain resume outcome requires protected inspection of its retained episode
and control state before another action. This is conditional mutation, not a
promise to reproduce every old command response forever. Automatic task progress
does not give an operator permission to invent a new resume budget. If its outcome
cannot be established, retain uncertainty rather than retry under a fresh revision.

Delivery requeue instead uses the approved caller operation ID, expected job
revision, selected validated delivery-policy revision, and atomic queue admission.
A matching protected operation returns the original result before revision/count
checks; argument reuse conflicts. The 64-per-job and 100,000 global protected
requeue-result limits, 128-byte ID and 2-KiB result bounds remain unchanged. Do not
apply that job policy to initialization, backup, inspection, or other commands.

Requeue preserves the delivery/origin identity, exact prepared bytes, target
binding, destination idempotency key, previous attempt results and content-expiry
anchor. It cannot requeue success, a live/in-flight round, logically expired
content, formation failure, or an unavailable/revoked binding. Server cooldowns
and physical rate/ownership gates remain in force. No network operation occurs
inside either administrative transaction.

## Protected inspection and finite command results

Initial inspection kinds are `summary`, `inputs`, `candidates`, `events`,
`deliveries`, `bindings`, `definitions`, `diagnostics`, and `maintenance`.
Listing is ordered by stable local opaque identity, with default and maximum
page size 100. A bounded cursor identifies installation, kind, filter, inventory
revision and last opaque key; it is not authorization or a source query. Reject
stale/mismatched cursors instead of pretending pages are one unchanged snapshot.
Never retain a SQLite read snapshot or the root lease between separate commands.

Default output is a versioned `cli-report/1` JSON object containing command kind,
success/failure class, closed safe reason code, and typed metadata. Business values,
raw records, credentials, secret reference contents, target URLs, arbitrary errors,
and raw HTTP responses are absent. Protected local object IDs are not permitted
as ordinary log fields or metric labels just because inspection can use them.

Content inspection kinds are limited to `deliveries` and `diagnostics`. Explicit
content inspection returns only one retained prepared payload or exactly retained
formatter projection, with completeness/expiry qualifications and encoded byte
length. Use base64 for exact prepared bytes so display does not reinterpret their
format. Missing/expired content is explicitly unavailable. Fully retained prepared
bytes can be retrieved without a compatible formatter; reproducing formation
requires compatible definitions/formatter and reports missing dependencies
separately. Do not rerender current
definitions, query history, reconstruct values, or send to make inspection useful.

Select a 1-MiB encoded command-result limit and 1-KiB cursor limit, not benchmarked
resource claims. Reserve buffers under the owning block budgets. Oversize requested
content is explicitly unavailable through this view; never clip and call it exact.
An unfinished page is marked limited with a valid continuation or failure, not a
complete inventory. Content output remains sensitive, even in this JSON envelope.
It is not a default diagnostic export or material to publish.

Inspection uses bounded reads and the existing five-second state-operation and
two-second snapshot limits. Finite administrative command invocations and offline
maintenance have a ten-minute cancellation budget; it does not guarantee OS I/O
return. This is not a lifetime limit on `run`: normal run continues until stopped
and retains the separate 30-second process/20-second delivery shutdown budgets.
Dry-run retains its own ten-minute source/workspace/request limits. A
timeout cannot release ownership while a worker or uncertain commit is unfinished.

## Gated operations, not force commands

The following need further concrete contracts/evidence before any implementation
advertises them as supported:

- Confirmed-history gap acceptance and observation-boundary changes: validate exact
  skipped coverage, preserve visible holes and existing obligations/protection,
  and never manufacture lifecycle proof or a new deduplication namespace.
- Restore preparation/review/activation: exact reconciliation input and durable
  recovery evidence must implement the already approved held authority/nonce
  two-gate publication protocol. A generic `--yes` is not reconciliation.
- Formation repair, candidate reprocessing, semantic correction, and full history
  replay: no implicit rerender/resend, expired-identity reconstruction, or fallback
  to new configured identities. Requeue and dry-run are not these operations.
- Identity-key rotation, source/target audience migration, incompatible interpreter
  or encoding transitions: no generic force/rebase/mark-compatible override.

A binary lacking a required path refuses it before dependent I/O. Unknown command
names/flags are argument errors, not a way to reach raw maintenance. Reserving a
topic here neither declares the transition supported nor closes its open decision.

## Exit outcomes and recovery

| Exit | Meaning |
| --- | --- |
| 0 | Requested operation completed with its documented effects; a known empty inspection result can be successful |
| 1 | Safe classified internal/I/O failure, not proof of rollback |
| 2 | Unsupported syntax, static configuration, or arguments; no operation admitted |
| 3 | Authority, compatibility, binding, conformance, or required activation gate blocked |
| 4 | Exclusive installation/workspace ownership unavailable |
| 5 | Requested retained object/content unavailable, expired, or not found |
| 6 | Expected-revision, protected-operation-argument, or cursor conflict |
| 7 | Finite capacity/work/result budget prevented complete execution; partial dry-run/page results are explicitly qualified |
| 8 | Interrupted or unknown mutation outcome requiring inspection before retry |

These outcomes supplement safe typed output, not raw exceptions. If an interrupted
mutation's result is unknown, exit 8 and preserve its operation/episode evidence;
do not report "failed, safe to repeat". Known committed success can be reported
without repeating the mutation. Process termination may prevent any final output;
on restart inspect retained authority/work, never infer rollback from missing text.

## Test criteria

- Every mode has instrumented negative tests proving forbidden state/secret/network
  operations never occur, including malformed arguments and failure cleanup.
- Native subprocess tests cover one owner, interrupted commands, stale revisions,
  unknown commit outcomes, root aliases, no live admin, and physically held locks.
- Compatibility tests freeze admitted closures, deadlines and bytes across every
  permitted edit; global limit reductions cannot delete obligations or grant an
  exception to new safety caps. Unsupported changes remain blocked.
- Requeue operation repeats, stale resume requests, depleted budgets, content
  expiry, cooldowns and retired scopes cannot mint budgets or redirect content.
- Redacted/content inspection, cursor changes, result limits and unavailable
  snapshots cannot leak secrets or mislabel reconstructed/partial content as exact.
- Backup/migration/compaction obey their existing staged-artifact, workspace,
  cancellation and authority contracts without implicitly implementing gated paths.

These criteria are not command implementations, conformance results, migration
contents, or a supported application/configuration artifact.
