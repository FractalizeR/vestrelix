# Configuration and process control

**Status: review-ready proposal; not approved. Not an implementation baseline.**

This block proposes strict configuration, recoverable semantics and bindings,
single-process ownership, activation, and isolated evaluation. It does not approve
application implementation, specify Go interfaces or SQL schemas, pin libraries,
or provide an implementation sequence. YAML field names and CLI syntax still
need a concrete specification consistent with this contract.

## Configuration boundary and validation

Propose one explicitly selected, versioned YAML document with typed settings for
inputs, extraction/detection profiles, rules, context-lookup bindings, routes,
output profiles, destinations, state, and process/operations settings. Adapter
settings belong to their declared type; portable rules do not contain arbitrary
source-query or transport option bags. Configured identities are stable and
bounded, not generated from subjects, addresses, credential values, or timestamps.

Reject unknown/duplicate keys, duplicate identities, unsupported versions/types,
wrong scalar types, dangling references, ambiguous input ownership, contradictory
profiles, and limits inconsistent with their owning block. Reject YAML aliases,
anchors, merge keys, custom tags, and multiple documents. There are no includes,
remote configuration, implicit environment substitution, shell commands, or
executable extensions. Explicit secret references are a separate typed mechanism.

Compile only bounded declarative conditions and the already approved restricted
formatting/extraction mechanisms. Initial condition forms are typed comparison,
presence/quality tests, approved domain matching, and bounded all/any/not groups;
regular expressions use Go's bounded supported syntax, not arbitrary callbacks.
Presence does not turn invalid/conflicting data into a valid value. Propose
conservative true/false/unresolved evaluation, without error-hiding short circuits:

| Condition | Result |
| --- | --- |
| Presence of valid value, including a valid null envelope sender | True |
| Presence of missing value | False |
| Required value comparison with missing/invalid/conflicting value | Unresolved |
| Presence of invalid/conflicting value | Unresolved; explicit quality tests may inspect its declared qualification without inventing a value |
| Not | Invert true/false; unresolved remains unresolved |
| All/any | Unresolved if any child is unresolved; otherwise ordinary boolean conjunction/disjunction |

Boolean simplification cannot turn an invalid required routing fact into a
broader audience or an intentional no-destination decision. Exact typed operators
need matching tests in the concrete specification. No general expression language
or user-supplied executable code is introduced.

Source filters and context-lookup bindings must satisfy the approved adapter
subset/escaping/coverage contract. Static parsing is not evidence that a source
API supplies complete results or that a Postfix profile proves generation identity.
Unverified profile/adapter capabilities remain activation gates.

Proposed additional loading limits, **not approved or benchmarked**:

| Setting | Initial proposal |
| --- | --- |
| Configuration file | 1 MiB |
| Parsed nesting / nodes | 16 / 10,000 |
| Single scalar | 64 KiB, subject to smaller field-specific limits |
| Configured inputs / rules | 16 / 64 |
| Configured identifier | 64 bytes of validated ASCII identifier characters |
| Condition nodes / depth per condition | 64 / 8 |
| Retained semantic definition objects / revisions per logical entity | 1,024 / 8 |
| Combined retained semantic-definition content | 16 MiB, also within global state capacity |
| Explicit binding revisions per logical input/destination | Eight, including the current revision |
| Resolved secret value / combined startup secret material | 64 KiB / 1 MiB |

The approved destination/route, template, JSON, memory, source, and state limits
still apply. Bound parsing before allocation, not only the decoded result. These
count limits do not promise that every object can simultaneously reach every byte
maximum or fit the reduced state budget.

Diagnostics use safe reason codes, line/column, known schema field names, and
bounded collection indices. Do not echo parser excerpts, scalar values, arbitrary
unknown keys, secret-reference contents, or complete configuration. An unknown
key itself may contain a secret and is not automatically safe as an error path.

## Distinct modes and side effects

| Mode | Permitted effects |
| --- | --- |
| Static validation | Read and check the selected configuration; no state open/initialization, secret resolution, network, or migrations |
| Explicit initialization | Create private installation control state, key material, and empty supported database; no source reads or sends |
| Normal run | Resume compatible authoritative state, admitting new work only after activation checks |
| Dry-run | Explicit bounded source reads and isolated processing/formatting; no production SQLite access or destination network operations |
| Inspection | Protected local read-only inspection under the initial offline administration policy |
| State-changing administration | Explicit maintenance, resume/requeue, or activation under exclusive process ownership |

A static validation success means structural/semantic checks passed, not that
credentials work, an endpoint is reachable, or an adapter passed conformance.
Normal run never implicitly initializes, migrates, restores, replays history, or
grants an exhausted task another budget. Initialization is not an escape hatch for
missing production state; replacement of an existing installation is not implicit.

Propose no hot reload initially. Edited settings and rotated external references
take effect only through a controlled restart and validation. Do not interpret
`SIGHUP` as permission to apply new settings; configuration-file changes alone do
not mutate running clients, existing payloads, or admitted definition snapshots.

Static invalid configuration prevents activation. A valid configuration with an
unavailable scoped binding or unsupported retained semantic version can leave
only the affected work paused when its dependencies are known; it does not
authorize fallback to current definitions. Unknown global state format or authority
stops all normal worker activation. Operations/readiness meanings remain a
separate block, not a promise that every partial startup is ready.

## Recoverable definitions and configuration changes

Propose storing minimal immutable validated semantic definitions in protected
SQLite, with stable logical identities, semantic-format/interpreter versions,
dependency references, and deterministic revision digests. Admission pins the
needed definition closure: extraction/normalization, rule/proof/lookup policy,
route/field/audience policy, templates, and output-profile semantics as applicable.
Persist required definitions with or before the atomic admission that references
them; no acknowledged work depends solely on a replaced configuration file.

Store validated nonsecret semantic data, not a full YAML, environment, client, or
credential dump. Nonsecret does not mean public: a query literal or field policy
can still contain private deployment information. Exact versioned canonical
encoding and compiler compatibility need evidence before digest comparisons are
used. Formatting/key-order differences are not new business identities, and a
digest match is not independent proof of semantic correctness or source coverage.

An executable retained definition requires a supported interpreter/profile
version. Missing/unsupported definitions pause dependent work visibly; never
reinterpret old expressions under a new meaning or substitute the latest
template. Ordinary deadlines/automatic expiry continue as approved. Definitions
remain pinned only while needed for retained work/protection or supported local
reproduction; state cleanup rechecks references before retirement.

Reaching a retained-definition count/byte limit rejects the incompatible new
activation/admission rather than evicting referenced definitions. There is no
automatic namespace reset, discard of old obligations, or unlimited revision
archive to make every edit acceptable.

| Change | Proposed behavior |
| --- | --- |
| Display label or nonsemantic description | Does not recreate events, jobs, budgets, or source progress |
| New route/template/allowed-field policy | Applies to newly admitted origins; already admitted candidates/jobs keep approved frozen semantics |
| New destination | Does not resend retained historical events automatically |
| Suspended input/rule | Stop its new reads/admissions as appropriate; retain existing progress/work and original automatic deadlines |
| Suspended/removed destination or revoked binding | Sending is blocked, including old jobs; selected obligations are retained, not silently changed to no-destination |
| Source view/query scope, extraction meaning, lifecycle/correlation identity, or rule identity semantics | Block affected incompatible progress/admission until an explicit supported compatibility decision exists |
| Secret rotation | Apply only after binding-continuity validation; reference name alone is insufficient |

Condition/template edits cannot silently rewrite a possibly sent payload. A
tightened field policy does not automatically erase old authorization snapshots:
an operator who intends to stop old disclosures must explicitly suspend/revoke
the relevant binding/work. Current revocation takes precedence over historical
definitions; retaining an old definition is not continuing permission to send.
Suspended destinations retain selected assignments under queue/capacity rules;
expiry and failed-delivery reporting remain automatic, not operator acknowledgments.

Initial compatibility decisions are closed, reviewed transitions for supported
profiles, not a general state-mapping language. An unimplemented transition stays
blocked. Historical replay, formation repair, and semantic corrections need
separate explicit contracts; creating another configured identity is not a safe
generic migration strategy.

## External references and actual binding continuity

Propose explicit references to private files or named environment values for
credentials and secret target URLs. Do not embed secret URL/token values in the
semantic snapshot or generic YAML scalar interpolation. File reads are bounded,
ownership/access checked, and errors redacted. Resolve needed values at startup
into bounded immutable objects; do not reread a changed file between attempt
authorization and transmission. Environment references resolve from the process's
fixed inherited environment, not an implicit environment-driven config overlay.

Configuration can declare a finite set of named binding revisions for each
logical input/destination, their external references, and current enabled/revoked
status. One revision is current for new work; older revisions can remain explicitly
available for frozen work. A previously admitted revision cannot be overwritten
with new target semantics. Removing/revoking it pauses dependent work; no silent
redirection to the current revision. Declaration is not proof of continuity.

Propose an installation-local 256-bit identity key in an owner-only file outside
SQLite. Initialize it explicitly once. A separate installation-bound key verifier
in private control metadata detects wrong/missing key material even when no
retained binding tags exist. Do not regenerate a key on startup, treat key loss
as fresh state, or automatically rotate it to make comparisons pass. Key backup
and any future key-rotation protocol require protected handling independent of
the database images; initial operation does not support implicit key rotation.

Use versioned, domain-separated HMAC-SHA-256 binding evidence over the exact
routing/source-sensitive values actually used. Distinguish source from target,
include applicable binding/profile identity, and use unambiguous bounded encoding.
Persist the tag and key/encoding version, not secret URLs or authentication bytes.
The resolver object owns both its verified tag and immutable connection values;
checking a tag for one set of values and sending another is forbidden. Tags and
key verifiers are private metadata, not log fields, metric labels, or capabilities.

For generic webhooks, the opaque target URL and any authentication/header values
that might select a recipient are binding-sensitive. Authentication can itself
select another tenant/audience. Excluding a rotating value as authentication-only
requires a verified profile contract proving audience continuity; generic support
and Pachca naming alone provide no such proof. Keeping old referenced values can
serve old jobs; replacing them with different values cannot.

For sources, changed credentials can change tenant or field visibility even when
the endpoint URL is unchanged. A changed source binding blocks affected polling
and old-candidate lookups until an explicit verified source-specific compatibility
contract establishes continuity of the authorized view. It cannot silently reuse
old frontiers/fingerprints under a differently visible source. Source identity
and acquisition progress remain owned by ingestion, not an HMAC namespace.

HMAC evidence checks local binding continuity without storing opaque secrets in
SQLite; it does not prove a receiver's behavior, server-side audience stability,
credential validity, or source completeness. Exact tag encoding, resolver tests,
and profile-specific rotation evidence remain conformance gates. Startup validates
retained evidence against the resolved revision before dependent work can run;
each attempt still checks that the same authorized immutable resolver generation
is enabled before it is charged.

## One authoritative process and state location

Propose an owner-only installation control root with a persistent OS advisory
lock file. On the supported Unix targets, a lifetime-held exclusive file lock is
the candidate mechanism. It must pass native contention/crash/path tests before
claiming enforcement. A PID file, SQLite writer lock, or expiring heartbeat alone
is not an active-instance fence.

Canonicalize the control root, validate ownership, and reject unsafe symlink,
hardlink, and replacement aliases for controlled files. Secure open/check behavior
must address path races on each supported target. Never unlink or replace the
lock file as stale-lock recovery. Hold its open lock until workers/connections
are stopped or the process exits; a dead process's kernel lock is released without
deleting the file. Inability to establish ownership fails closed.

Normal run, initialization, mutating administration, and initial inspection all
use the same control root and exclusive ownership policy. Propose offline local
administration/inspection initially: they refuse while normal run owns the root,
rather than commanding it to stop or introducing a public admin HTTP/IPC service.
Static validation can run alongside production because it has no processing/state
side effects. Monitoring endpoints belong to operations, not this admin surface.

An owner-only authority manifest names one authoritative database identity and
generation within that root, installation identity, and active/held status. The
supported application selects state through this manifest, not an arbitrary bare
database pathname. Missing, corrupt, mismatched, or uncertain authority metadata
stops activation; never scan for the newest apparently suitable database.
Initialize/publish authority only after required private key and database state
are durably valid. Incomplete initialization is recoverable only through the
explicit initialization path, not normal run's fallback.

### Restore hold and authority publication

Restore holds exclusive root ownership, preserves the original as inactive, and
prepares a new generation with a fresh activation nonce. Backup activation
evidence is never sufficient to activate its restored copy. Establish durable
restore hold in the replacement before publishing authority that points to it;
the new authority remains held until explicit reviewed activation.

Activation requires exact matching installation/database/generation/nonce
evidence in committed database state and the authoritative active manifest.
After operator reconciliation, commit matching activation evidence first, verify
that outcome, then durably publish the manifest's release for that generation.
A crash between those steps still leaves the manifest held. Unknown commit or
publication outcomes must be resolved explicitly, not assumed successful or
automatically released. This is a recoverable two-gate protocol, not a claim of
an atomic transaction across SQLite and an external file.

Confirm the old generation/process is no longer authoritative/active before
release; preserved old images cannot run through the same manifest. Ordinary
restart or migration cannot remove restore hold, accept unknown source coverage,
or acknowledge external delivery reconciliation. Arbitrary whole-directory copies
on another path/host remain an operator deployment boundary: a local manifest/
lock is not distributed fencing or clone detection.

Propose an additional 768 MiB managed offline maintenance-workspace budget, with
at most one inactive preserved generation and one restore candidate, including
their WAL/temp/staging overhead. It is not extra normal-run database capacity.
It is separate from the approved 384 MiB working budget and 1 GiB backup-area
budget, but all areas count against real volume free space/reservations. Existing
inactive copies and crash leftovers consume this allowance. No safe workspace
means restore/compaction is refused; never exclude retained generations from disk
accounting or delete the last needed original automatically to make room.

## Bounded isolated dry-run

Propose a dry-run with an explicit source interval and finite operation budget.
It evaluates the approved source/detection/routing contracts against separate
empty temporary state, not a production database copy containing live delivery
jobs. It cannot acknowledge production progress/jobs, resume production tasks,
perform administrative mutations, or construct a destination HTTP sender.

Initially dry-run obtains the same installation-root ownership lease as normal
run, without opening production SQLite, reading the identity key, or loading
target secret references. Thus it does not run alongside production for that
installation and cannot double its source concurrency through an independent
process-local limiter. Required source references are read-only credentials;
source lookup/subdivision work shares the dry-run's source request/buffer budgets.

Use a separate managed private dry-run root with exclusive workspace ownership
and a 64 MiB aggregate DB/WAL/temp/artifact budget. Canonical path checks reject
production state/backup/maintenance areas and unsafe aliases/nesting. A crashed
workspace counts until safely cleaned; another invocation cannot manufacture a
fresh allowance by choosing a different workspace within that root. Copies of an
entire installation/dry-run root are outside the local enforcement claim.

Propose ten minutes and 64 physical source requests per invocation, including
lookups, subdivisions, and retries. Per-request time/size, candidate deadlines,
and shared memory limits still apply; simulated work cannot receive infinite
fresh budgets. Partial/limited/proof-unresolved results are explicit, not a claim
that live processing would certainly produce the same notifications.

Default output contains counts and safe classifications. An explicit protected
local preview can show permitted prepared content, never trigger a send. It is
potentially sensitive operator output, not ordinary logs or an export safe to
publish. No production target reachability/conformance claim comes from preview.
Temporary cleanup is best effort after interruption; leftovers stay private and
budgeted. No additional file-input adapter or source-mirroring feature is implied.

## Startup, shutdown, and maintenance recovery

Startup validates settings, establishes authority/ownership, checks database/key/
engine/format compatibility, resolves allowed bindings, and durably registers
required definitions before dependent workers can admit work. Scoped pause
reasons remain observable. Source requests and POSTs are never validation probes.
Already committed progress, deadlines, quotas, ownership, and cooldowns govern
recovery; restarting does not replenish them.

On `SIGTERM`/`SIGINT`, stop new reads/admissions/attempt claims first. Preserve the
approved delivery drain of at most 20 seconds and propose a 30-second overall
process drain budget. Cancellation and final commit resolution retain ownership
until workers stop; a timeout never declares them successfully completed. If the
process must terminate, open work recovers under its durable interrupted-work
contract. OS I/O can outlast cancellation, so a supervisor's hard kill is not proof
of clean shutdown. Do not release the root lock to another process while live
workers remain capable of sending.

Maintenance uses explicit finite operation deadlines and its own bounded staged
artifacts/recovery evidence, not an unbounded global command framework. Propose
ten minutes per maintenance invocation, with cancellation/unknown-outcome handling
as in the state contract, not a guarantee of system-call return within that time.
The approved operation-ID/64-per-job requeue protection applies to retained job
requeue only; it does not invent a job identity for init, backup, restore, or
inspection. Interrupted initialization, migration, publication, and restore have
their specific authority/version gates and never fall back to normal sending.

## Proposed test criteria and evidence gates

- Strict YAML tests cover duplicate/unknown keys, aliases/tags/merge/multidocument,
  oversized/deep structures, incorrect types and references, and safe diagnostics
  that do not echo unknown keys or parser excerpts.
- Condition truth tables preserve unresolved data under negation/grouping, field
  quality, and routing. No expression/template can reach secrets or executable
  environment/application objects.
- Restart recovers pinned semantic closures, compiler versions, immutable payloads,
  and explicit old binding revisions. Edited policies, unsupported versions,
  suspension/revocation, missing definitions, and retention pressure cannot expand
  audiences or silently reset identities/progress/budgets.
- Actual resolver values and binding tags are inseparable. Secret-file replacement,
  same-name reference changes, authentication selecting another tenant, source
  visibility changes, missing/wrong key, and unverifiable rotation fail safely.
- Real temporary state and subprocess tests on each native target cover competing
  owners, alias/hardlink/path races, crash release, persistent lock files, and
  refusal of offline admin while normal run is active.
- Initialization/restore crash barriers cover database evidence commit, authority
  publication, held/active state, and nonce mismatch. Restored old activation
  evidence cannot enable sends; failed publication never selects another image.
- Dry-run never opens production SQLite, reads target secrets, builds a sender,
  acknowledges production work, or bypasses source limits through a concurrent
  normal run. Managed-root/orphan accounting, preview privacy, and interruption
  cleanup preserve isolation under failure as well as the happy path.
- Shutdown and interrupted maintenance preserve physical/durable ownership and
  finite budgets without implying successful completion or automatic restore
  activation. Workspace exhaustion refuses work without deleting protected data.

These are proposed criteria, not implemented commands/tests or established native
behavior. Exact YAML/CLI and definition/tag encodings, path/lock/authority storage
mechanisms, supported semantic transitions, and profile conformance remain gates.
Operations/health/metrics require their own individually approved block.
