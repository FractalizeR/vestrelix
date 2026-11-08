# SQLite state lifecycle

**Status: approved block contract. Not implemented or driver/storage-conformance-verified.**

This block defines how one local SQLite database preserves domain transitions,
bounds retained state, retires content without silently losing obligations, and
supports maintenance and recovery. The project owner approved its retention,
capacity, maintenance, and automatic-expiry policy with reduced storage defaults.
Approval does not establish driver/storage conformance or authorize implementation.
There is no SQL schema, migration implementation, Go interface, or implementation
sequence here.

## Ownership and durable boundaries

Domain blocks own transition meaning. Processing coordinates common acceptance
and finalization; `sqlitestate` executes their durable consequences. It does not
interpret Postfix, select recipients, invent retry policy, or independently commit
one domain's part of a common transition.

| Transition | Atomic consequences |
| --- | --- |
| Accept a complete polling unit | Replay markers, context/candidate updates or explicit outcomes, necessary follow-up work, and compatible progress |
| Finalize an occurrence/notice | Stable event/case and routing decision, all selected assignments and prepared content or explicit failure dispositions |
| Start/finish an attempt | Approved ownership, counters, deadlines, and conditional outcome/retry/cooldown changes |
| Admit manual requeue | Operation protection/result, expected-revision decision, queue slot, and new finite round |
| Expire retained content | Eligible terminal/expiry disposition, necessary minimal identity/audit protection, and removal of permitted content |

No acknowledgment precedes the relevant commit. No network operation or message
rendering runs inside a write transaction. A large polling unit cannot be partly
accepted merely to fit storage: safe subdivision must re-read source-specific
units under the existing ingestion protocol and inherited budgets, or admission
blocks without advancing that unit's progress.

Resolve unknown commit outcomes through retained transition/operation identities
and expected revisions. A timeout, canceled context, or connection error is not
proof of rollback. Do not retry a mutation until its durable outcome is known;
do not retry a POST simply because its result could not be saved. The domain's
existing token/budget rules still apply. There is no durable progress claim if
even the failure disposition cannot be saved.

## Local storage, startup, and privacy

Use a regular local filesystem with working locking, synchronization, and
atomic file-publication behavior. Network filesystems, synchronized cloud folders,
and access from multiple hosts are unsupported. A container needs suitable local
persistent storage; an ephemeral filesystem does not become durable because the
application calls commit.

Process control must establish the single-active-instance gate before state
mutation, migration, or restore. SQLite's writer lock is not that process fence.
Canonical-path/alias handling and activation of one authoritative state location
remain process/configuration gates; do not claim detection of arbitrary copies
of the database on another path or machine.

Startup checks database/application identity, supported state-format and migration
history, engine capabilities, private permissions, and required connection
settings before workers perform source or delivery I/O. A missing expected
database, unknown/newer format, drifted history, or corruption stops normal
startup. Fresh initialization is explicit; never silently recreate missing state
and start sending historical notifications again.

Use an owner-only state directory and files, equivalent to directory mode
0700 and file mode 0600 on supported Unix targets. The boundary includes database,
WAL/shared-memory files, temporary artifacts, diagnostic copies, and backups.
Validate existing ownership/access rather than trusting only creation defaults.
SQLite is not encrypted by this choice: host/volume encryption and backup access
control are deployment responsibilities. No new encryption or secret-store
dependency is introduced.

Retain only necessary facts, prepared content, protected identity metadata, and
safe operation results. Hashes, recipient-derived keys, and progress coordinates
are not automatically anonymous or suitable for logs/metric labels. Credentials
and secret target URLs remain external. Required immutable nonsecret semantic
definitions stay recoverable while referenced; storing only revision numbers is
insufficient. Configuration owns their validated representation and compatibility
contract, not an unrestricted configuration dump in SQLite.

## Durability, concurrency, and bounded work

Use WAL mode with `synchronous=FULL`, verified after opening every relevant
connection, and enabled foreign-key enforcement. Require the supported macOS
engine/VFS combination to honor the applicable full-sync/checkpoint full-sync
settings; refuse to claim equivalent power-loss durability without evidence.
Read back settings where possible instead of assuming an option was accepted.
Supported embedded SQLite builds must include applicable upstream correctness
fixes, including WAL-reset fixes; driver/version selection still requires review.

Commit recovery depends on correct filesystem/device synchronization. Process
kill tests demonstrate interruption recovery, not proof against every power
failure, controller cache fault, disk loss, or host compromise. A checkpoint is
not required to make a correctly synchronized WAL commit logically durable; the
WAL remains part of persistent state until SQLite retires it safely.

Use one serialized writer connection and at most two bounded read connections.
State-dependent decisions either run under the writer's transaction or validate
their starting revisions there. Uniqueness of occurrence/delivery/operation
identities and referential consistency must be enforced durably, not solely by
in-memory checks. No executable SQL from configuration, dynamic extensions,
cross-database atomicity through attachments, or independent adapter databases.

Approved, not benchmarked, routine-work limits:

| Setting | Initial value |
| --- | --- |
| Waiting writer commands | 32, with 32 MiB aggregate retained-buffer budget |
| Retained logical mutation content per transaction | 32 MiB |
| Routine state-operation deadline | Five seconds, including queue wait |
| Read snapshot / lock-busy wait | Two seconds / one second, within the operation deadline |
| Cleanup turn | Up to 100 objects and 250 ms planned work |
| Cleanup scheduling interval | One minute, without accumulated tick jobs |

Shared/reserved buffers can transfer ownership rather than be copied, but count
all held content against the relevant budgets. A count limit alone cannot admit
32 maximum-sized commands independently. Work expired in the writer queue never
starts mutation. Give due completion/recovery work bounded priority over new
admission without starving cleanup.

These time limits are cancellation/scheduling budgets, not guaranteed fsync or
system-call return times. An operation may finish after cancellation; retain its
ownership until it stops and resolve its commit status before replacement. The
250 ms cleanup budget does not promise that commit finishes within 250 ms.
Long maintenance has separate explicit finite operation budgets and no normal
worker activity; no implicit unlimited busy/retry loop is allowed.

The transaction-content ceiling is not a file/WAL-growth estimate. Indexes, page
rewrites, references, and SQLite bookkeeping also need space. A valid 5,000-record
source response may expand into much more than 32 MiB of delivery content and
therefore fail durable admission despite fitting ingestion's response limits.
It must safely subdivide through ingestion or block, not partially commit an
arbitrary prefix, clip payloads, or obtain fresh acquisition budgets.

## Retention: content, obligations, and identity are different

The approved upstream contracts remain in force: ordinary mail context expires
seven days after validated relay receipt; an admitted candidate can pin its
minimal required snapshot through its fixed three-hour deadline. Auxiliary
formatter-failure snapshots remain limited to 32 KiB, 24 hours, and 16 MiB
aggregate. Delivery attempt detail remains the latest 32 entries, at most 2 KiB
each. None of those limits expires a live delivery obligation.

Use these additional content-retention rules:

| State/content | Retirement eligibility |
| --- | --- |
| Active acquisition, candidate, delivery round, or physically unfinished attempt | Never removed merely by a storage TTL; the owning program component automatically resolves/expires it under its existing contract before cleanup |
| Successful job prepared content | Seven days after durable success, subject to remaining references |
| Finalized normalized event content | Seven days after all assignments reach durable terminal dispositions; explicit no-destination finalization closes this condition immediately |
| Formed undelivered job content | Thirty days after its first terminal non-delivery disposition, except a previously admitted live round pins necessary content through its budget |
| Terminal unresolved candidate's minimal inspection content | Thirty days after its terminal disposition, subject to existing reference/content restrictions |
| Formation-failed assignment | Thirty days of safe failure metadata; exact inputs only while independently retained event/definition data or the approved auxiliary snapshot remain available |

There is no new 30-day copy of formatter-failure inputs. Independent normalized
event facts and definitions have their own dependency lifetimes; diagnostic
expiry can legitimately make exact reproduction unavailable. Failed-assignment
metadata must say so rather than invent a snapshot from current configuration.

An eligible failed job becomes visibly expired/non-retryable with a retained
minimal outcome and aggregate expiry accounting before its content is removed.
This is an explicit retention disposition, not successful delivery or silent loss
of active work. A manual round admitted before content expiry pins what it needs
until it resolves; it does not refresh the original content-retention anchor.
Requeue admission checks logical expiry even if cleanup has not yet physically
removed the bytes. A new round cannot revive already expired content.

Pauses do not extend approved candidate/round deadlines. If the owner cannot save
an expiry transition because the store is unavailable, the old obligation and
necessary content remain; cleanup cannot assume that expiry was committed.
An expired candidate does not establish mail failure, and a failed delivery does
not become successful through retention.

Ordinary deadline/budget exhaustion and later retention cleanup do not require
operator approval. The owning program component saves the terminal outcome,
updates safe logs/metrics and eligible bounded notices, and cleanup retires
eligible content automatically. Explicit operator action is needed for a fresh
retry budget or exceptional recovery, not to acknowledge each expired job.

### Record replay markers and paused inputs

Retain record fingerprints for at least 24 hours after durable
acceptance, and longer until their compatible source-search region is below the
committed settlement frontier and no live acquisition/uncertain transition can
still revisit it. Pruning is conditional on the exact supported source/view
contract, not a record's mail timestamp or wall-clock age alone.

Discovery may have accepted records beyond settlement. A paused input therefore
keeps protection for its unsettled accepted region even after 24 hours. A simple
TTL cannot silently turn ordinary resume into unprotected replay. Keep a durable
retirement/coverage floor so a requested read below retired protection cannot be
treated as an ordinary supported resume. Advance it atomically with eligible
marker retirement; no hidden holes in the declared protected range.

History lookups do not re-ingest unrelated events under the approved contract.
Moving observation start, changing source view, or requesting historical replay
needs the separate compatibility/reprocessing decision. It cannot bypass retired
protection by minting another input identity. If safe retirement cannot be proven,
keep necessary markers; finite storage may then stop new admission.

### Business/terminal identity and manual-operation protection

Use a minimum 30-day retention for minimal occurrence, terminal-case, and
delivery identity protection, anchored at the latest relevant durable terminal
disposition or admitted manual action. Retain longer while referenced or while
supported ordinary processing can still recreate that occurrence. Preserve only
the keys/qualifications needed to recognize old work, not expired message content.

Passing settlement and pruning a source fingerprint does not prove that another
later record cannot describe the same occurrence. Detection/processing must
establish the safe retirement condition for business/terminal identities. Without
that proof, pins remain and capacity can block new work. Thirty days is minimum
eligibility, not a maximum history guarantee or automatic permission to resend.
Any explicit decision to discard still-needed protection changes guarantees and
must be observable; ordinary cleanup cannot make that decision.

For manual requeue, allow at most 64 accepted operations per retained job and
100,000 protected mutation results globally. Bound each operation ID to 128 bytes
of validated non-sensitive ASCII and each retained typed result to 2 KiB. Scope
uniqueness by operation kind, retained job identity, and operation ID; expected
revision/arguments are checked against that operation, not new identity fields.

Look up accepted operations before applying revision/count limits: a matching
repeat returns its original result, even at capacity, without another budget.
Reuse with different arguments is a conflict. New operations beyond the limits
fail before admitting a round. Rejected requests have no accepted state-changing
operation result or budget; do not retain an unbounded cache of arbitrary rejected
IDs. These limits do not restrict read-only inspection.

Keep accepted-operation markers, round numbering, and required audit protection
through the retained job/identity lifetime. The 32-entry diagnostic window cannot
evict them. Retirement requires the same reference/identity checks, not a separate
short TTL that would let an old command create another round. A forgotten job
cannot be recreated by requeue; historical reprocessing is a different contract.
Counter overflow stops the affected operation rather than wrapping protection.

## Capacity, WAL growth, and backpressure

The following reduced storage defaults are **approved, not benchmarked**:

| Setting | Initial value |
| --- | --- |
| Main database page-count size ceiling | 256 MiB |
| Managed working-file budget | 384 MiB for main database, WAL/shared-memory, and state temporary files |
| Working-family admission high-water | 90% of that budget |
| Main-page control/completion headroom | 32 MiB inside the main-database ceiling |
| Host-volume free-space admission floor | 128 MiB, in addition to the operation's reservation |
| Checkpoint trigger / WAL admission stop threshold | 8 MiB / 32 MiB |

These are ceilings/admission controls, not upfront disk allocation or expected
usage. Count limits in other blocks remain independent maxima: storage can stop
admission well before every queue/context/operation reaches its count cap. Large
alert volume is an observable pressure condition, not a reason to grow storage
automatically or silently discard protection.

The main page-count ceiling limits the main database, not WAL, temporary files,
or backups. Admission checks projected page use including required indexes and
retains the main-page headroom for bounded completion/control/cleanup work.
Working-family accounting includes actual allocated files; reusable free pages
and logical retained content are tracked separately. Deleting rows does not
necessarily shrink a file or release host disk space.

The family budget/high-water and WAL thresholds are admission controls, not a
claim that periodically measuring files enforces an exact physical hard cap.
Validate a finite per-write page/WAL amplification bound and reserve space before
each write class, including housekeeping. The 32 MiB logical-content ceiling is
not that bound. Do not enable the claimed bounded configuration before the chosen
engine/schema/transaction workload establishes it. A filesystem/quota can be a
last-resort hard backstop whose exhaustion fails closed, not successful retention.

Checkpointing runs through the serialized writer. Use bounded passive progress
normally; at WAL pressure, stop new admission, end supported read snapshots, and
provide reader gaps for checkpoint/reset. A partially successful checkpoint need
not shrink the allocated WAL file. Resolve pressure using actual reusable/growth
state; explicit truncation/compaction needs safe quiescence. `journal_size_limit`
is not a hard bound while readers or a large write keep the WAL live.

Reserved headroom is admission accounting, not guaranteed emergency disk space.
In-flight outcome commits and cleanup need their own bounded reservation; they
cannot write unconditionally because they have priority. If the store cannot
record a safe attempt start/result, no new network work is justified. Reaching a
global limit can pause otherwise healthy inputs/destinations; per-destination
isolation does not promise independence from global disk exhaustion.

On full/read-only/I/O-failed/corrupt storage, stop affected durable transitions and
new dependent I/O, retain known progress/obligations, and expose safe external
diagnostics where possible. Never delete active work, reset state, advance a cursor,
or claim rollback/success just to escape pressure. Capacity recovery revalidates
state, reservations, pins, and settings; it does not restore exhausted budgets.
An input whose retry budget already required explicit resume still requires it.

## Cleanup and physical data lifetime

Cleanup selects a bounded batch, then rechecks references, owner state, deadlines,
and revisions within the writer transaction. Deletion, explicit content expiry,
required tombstones, and protection-floor changes commit consistently. Count
associated rows/bytes, not just root objects; large cascades cannot bypass the
per-turn or mutation budget. Do not hold one scan snapshot indefinitely or enqueue
one task for every elapsed cleanup tick.

Ordinary cleanup reuses free pages; routine full-database vacuum is not assumed.
Compaction is explicit offline maintenance with verified backup, workspace,
finite operation budget, and quiesced workers. Never manually delete WAL files to
reclaim space. Cleanup interruption cannot remove an obligation without its
durable disposition or lose identity while still claiming its protection.

Logical deletion is not secure erasure. Old values can remain in free pages, WAL,
backups, filesystem snapshots, storage caches, or SSD remapping. SQLite retention
does not guarantee physical deletion at an exact time. Expose eligible versus
pinned ages, expired content, protected marker counts, file/WAL pressure, and
cleanup failures using bounded safe labels, not content or per-object identifiers.

## Migrations and integrity recovery

Use explicit offline upgrades before normal workers run. Quiesce operations,
hold the process/state maintenance gate, verify capacity and a consistent
pre-upgrade backup, then apply only the binary's supported forward migration path.
The preliminary Goose selection is an executor, not proof of compatibility,
automatic checksum validation, or safe rollback of external effects.

Require ordered migration identities and an application-verified immutable
definition/digest manifest. The concrete stored representation is a later schema
decision. Initially permit only migrations whose data changes and version marker
commit transactionally together. No manual "mark applied," automatic downgrade,
silent rebuild, or nontransactional destructive transformation is accepted.

An interruption before a migration commit leaves its old step; after commit the
exact new step is recognized. A valid committed prefix can resume along the same
verified path, but the process stays unready until the complete target format is
valid. Unknown history, changed applied definitions, or a failed integrity/
referential check stops activation. Integrity checks have explicit finite
maintenance budgets; cancellation is failure to finish validation, not permission
to skip it. Do not run raw repair or replace the database automatically.

Ordinary crash recovery of a transactional migration is not backup restore.
Rolling back through a backup is the separate state-loss operation below, with
different external-effect risks. Detailed version paths, migration contents,
driver behavior, and native-target recovery evidence remain prerequisites.

## Consistent backups and explicit restore

Use explicit local, offline backup as the initial supported operation; no
periodic backup scheduler, cloud adapter, or promised recovery-point interval.
Use a SQLite-supported consistent backup mechanism after quiescing workers, with
a validated driver mechanism. Copying a live main file alone or manually
assembling/deleting WAL files is not supported.

Create one private staged image, validate identity/schema/integrity and required
snapshot metadata, then durably close/synchronize and publish it as complete.
The manifest includes database identity, format/history, snapshot time, and
necessary semantic-definition references, not credentials. A checksum detects
accidental image changes, not malicious modification by someone with file access.
Compatible external definitions/bindings must remain recoverable separately;
an intact SQLite image alone is not proof of a complete system backup.

Keep at most two published managed images plus one in-progress image, each
limited to 256 MiB, within a separate 1 GiB backup-area budget including manifests
and temporary overhead. The backup area may share the working volume: account
for aggregate real free space, not independent imaginary reservations. A crashed
staging artifact consumes the same single staging allowance until inspected and
safely discarded; restart cannot accumulate another full image per attempt.

Seven days makes an ordinary image eligible for age-based retirement. It is not
a maximum data lifetime or a promise of seven days of backups. Preserve the last
verified image and any image protecting an unfinished upgrade until safe
replacement/release. At capacity, an explicitly requested new backup can rotate
the oldest unprotected ordinary image after its staged replacement has been
verified and synchronized, while keeping at most two published images. Never
remove the only verified/protected backup to make a required migration backup
appear possible.
If no safe room/rotation exists, backup or upgrade is refused. Never delete unknown
operator files or exports outside this managed inventory.

Backup cancellation, failed validation, or publication failure preserves prior
verified images and does not permit a dependent upgrade. Storage loss can still
destroy both state and backups on the same device; encrypted independent copies
and recovery-point objectives remain deployment responsibilities.

Restore is explicit offline maintenance into a separately validated state
location, with sufficient additional space and the original preserved. Never mix
a restored main image with another generation's WAL. Establish a durable restore
hold before the restored copy can be activated; restart and migration do not
remove it. Confirm that the original copy is no longer authoritative/active before
activating the replacement. The process/configuration block must specify this
activation mechanism; a file lock on one path cannot fence a second copied path.

A backup may predate accepted source records, sent notifications, consumed retry
budgets, cooldowns, and manual-operation results. Restore can therefore lose work,
repeat side effects, or roll back protection that ordinary restart preserves.
Keep source/delivery I/O held until the operator reconciles the snapshot's known
coverage and retained definitions/bindings and explicitly accepts unresolved
duplicate/loss risk. Database integrity is not external delivery reconciliation.
Do not invent success, assume source history still exists, or use a new database
identity as a silent fresh deduplication namespace. Arbitrary copied databases
cannot be detected automatically; the supported restore path must enforce its
hold and authoritative-location transition before releasing workers.

## Test criteria and evidence gates

- Real temporary SQLite tests cover every common atomic boundary, cross-input
  context contention, uniqueness/reference enforcement, uncertain commits, and
  cancellation without competing replacement mutation/send ownership.
- Supported native targets verify actual connection settings, crash recovery,
  engine correctness baseline, bounded reader gaps, WAL pressure, busy/full/I/O
  failures, and finite write amplification/reservations. Kill tests do not claim
  to prove power-loss durability of arbitrary hardware.
- Context/candidate pins, active attempt ownership, content expiry, failed-job
  manual rounds, no-destination events, and auxiliary diagnostic TTL remain
  distinct. Cleanup races cannot delete newly referenced or still-active state.
- Normal deadline/budget exhaustion and eligible retention cleanup complete
  automatically with safe observability, without an operator acknowledgment.
- Paused inputs keep unsettled replay protection. Safe frontier retirement differs
  from business identity retirement; later records for the same occurrence cannot
  resend it after a blind TTL. Unprovable retirement causes visible pressure.
- Operation-ID repeats/conflicts, stale revisions, 64-per-job/global limits,
  byte limits, and diagnostic-history eviction preserve exactly the retained
  idempotency horizon without minting extra retry budgets.
- Dense accepted source responses exceeding durable mutation capacity either
  safely subdivide under original budgets or block without partial acceptance.
  Page reuse, WAL allocation, cleanup cascades, and staging leftovers count toward
  real capacity rather than merely logical payload totals.
- Migration interruption before/after each commit, changed manifests, unsupported
  versions, failed integrity checks, canceled backup, and valid committed prefixes
  cannot bypass activation gates or silently rebuild state.
- Backup/restore round trips preserve consistent state and private permissions.
  Old snapshot external-effect ambiguity, a durable restore hold surviving restart,
  original-copy activation conflicts, exhausted workspace, and failed publication
  have explicit safe outcomes, without live destinations or operational data.

These are approved acceptance criteria, not implemented tests, measured resource
limits, or a claim of driver/storage conformance. Configuration recovery,
single-instance/restore activation, and concrete schemas/migration paths remain
explicit cross-block gates; no implementation is authorized by this contract.

## Public references

- [SQLite WAL, checkpoints, and persistent files](https://www.sqlite.org/wal.html)
- [SQLite synchronization settings](https://www.sqlite.org/pragma.html#pragma_synchronous)
- [SQLite maximum page count](https://www.sqlite.org/pragma.html#pragma_max_page_count)
- [SQLite journal size limit](https://www.sqlite.org/pragma.html#pragma_journal_size_limit)
- [SQLite backup mechanisms](https://www.sqlite.org/backup.html)

These describe SQLite behavior, not validation of a selected Go driver, host
filesystem, migration path, or device power-loss behavior.
