# Routing and formatting

**Status: review-ready proposal; not approved. Not an implementation baseline.**

This block selects destinations and permitted fields, forms destination-specific
messages, and supplies durable delivery assignments. It does not send requests,
execute source queries, decide mail failures, or own network retry schedules.
The approved detection contract does not approve the new choices below.

## Input and output contract

Input is a complete normalized business event, or a durable processing/system
error case that its owner has made eligible for notification. Raw records,
arbitrary exception objects, and unproven business candidates are not messages.

Business events and error notices have tagged, stable origin identities. An error
case is not a successful mail event, and its identifier does not substitute for a
source record, correlation key, or business event identity.

| Result | Meaning |
| --- | --- |
| Explicit no destination | Valid conditions intentionally select nobody; no delivery is claimed |
| Formed assignment | One logical destination and an immutable, bounded payload are ready for durable admission |
| Formation failure | A selected assignment remains visibly undelivered; no malformed/raw substitute is sent |
| Audience unresolved | Required routing facts are invalid/missing; no audience is guessed |
| Notice suppressed by policy | Secondary error notification admission was explicitly limited; the underlying failure remains observable |
| Undelivered due to capacity | A destination's automatic queue cannot admit the selected work; retain its failure under the state policy |

Multiple conditions may select the same destination, but one origin has at most
one initial assignment to that logical destination. Repeated selection is not
permission to send several message variants. Conflicting definitions for that
origin/destination fail validation rather than choosing the last matching route.

## Frozen definitions and destination identity

Propose fixing the applicable route, template, field policy, and audience-binding
definitions when the originating candidate or notification case is first durably
admitted. Finalization uses those definitions, not the configuration current after
a three-hour wait. Their recoverability is required; storing revision numbers
without recoverable semantics is insufficient.

Provisional candidates retain their original snapshots when merged into a proven
occurrence. Compatible snapshots preserve the original applicable definition;
they are not assembled into a union of recipients or fields. Incompatible
route/template/audience definitions leave visible unresolved work pending an
explicit compatibility decision. Acquiring an event ID does not authorize a new
configuration snapshot or selection of the latest revision.

A logical destination has a stable ID and a versioned audience/target binding.
Secrets stay external. A job retains the required binding revision and credential
references, not a secret webhook URL or authentication values.

Resolving a reference must establish the same authorized target/audience, using
immutable binding definitions or equivalent retained identity evidence. An
unchanged reference name alone is not sufficient if its contents were replaced.
Authentication rotation and recipient changes are distinct. If a secret webhook
URL encodes both, a change cannot be assumed to be authentication-only. Missing,
revoked, or unverifiably changed bindings pause old work rather than redirect it.
The concrete recoverable-definition mechanism belongs to configuration/state
design; no new secret store is introduced here.

## Selection, audiences, and notification kinds

Routes use bounded conditions over declared normalized facts. Selection may
inspect facts that are not permitted in an outbound payload; inspection does not
grant permission to forward them. Unsupported conditions or unknown field names
are configuration errors. A runtime-invalid required condition is explicit
unresolved routing, not a silent match, catch-all, or intentional no-destination
decision.

Propose separate destination capabilities, both disabled by default:

| Kind | Eligibility |
| --- | --- |
| Business event | Ordinary route conditions and that destination's business field policy |
| Event-related processing error | Processing-error opt-in, with sufficient valid context to prove the intended audience |
| System/operational notice | System-destination designation and a curated operational field policy |

A destination can have both capabilities, but this does not merge the policies or
duplicate one notice. Processing-error opt-in does not subscribe it to all system
faults. System designation does not grant access to every event's subject,
addresses, or raw evidence.

If missing or ambiguous context prevents establishing an error's business
audience, do not notify ordinary destinations merely because their error opt-in
is enabled. Only an eligible system destination can receive the safe operational
description. The owner decides when an error is terminal or notification-ready;
routing does not turn every partial observation into a failure.

Initial error projections permit only declared safe codes, component and
configured input/rule/destination identifiers, counts, and age. They do not
automatically include subjects, addresses, SMTP diagnostics, arbitrary exception
text, URLs, headers, or source/event identifiers. More detailed disclosure needs
an explicit audience and field-policy decision, not a template fallback.

## Field projection and semantic fallback

Construct the destination's allowlisted projection before evaluating any message
template. Do not pass the full event and then remove fields after rendering.
There is no wildcard projection or raw-record fallback. Unknown references fail
configuration validation; a required permitted value unavailable at formation
produces a visible formation failure, not an empty or invented value.

The first mail notification retains only envelope sender, rejected envelope
recipient, decoded subject, and outbound relay receipt time. Context and evidence
metadata do not become extra message fields just because detection retained them.

Fallback selection belongs to the approved extraction semantics. Formatting does
not silently repair invalid values with another meaning. If a configured variant
permits an effective sender originating from header `From:`, its supported
representation must retain that qualification: an annotated display value or a
profile-defined value-plus-origin representation. Do not expose an unqualified
raw effective value that templates can present as envelope sender. If the target
profile cannot preserve required origin information, formation fails.

Canonical envelope facts remain unchanged. An arbitrary natural-language literal
cannot be automatically proven truthful; the enforceable contract is to retain
the selected value's semantic qualification in supported rendering paths. The
envelope-only first scenario is not weakened by a generic fallback capability.

## Bounded JSON and text formatting

Propose a fixed JSON structure made from literal keys, bounded objects/arrays,
literal values, and references to permitted typed fields. Serialize values using
`encoding/json`; do not build arbitrary raw JSON by interpolating source strings.
Field names, nesting, and repeated structure come from validated configuration,
not unbounded source data.

For string interpolation, use the standard `text/template` parser with a narrow
accepted syntax: literal text and direct permitted scalar references only. Reject
function/builtin calls, indexing, methods, loops, recursion, definitions, template
invocation, and access to files, environment, configuration, or the current clock.
Validate the parsed representation rather than stripping suspicious text. Supply
only inert projected values, never application objects, functions, or credentials.
This is not a general-purpose template/plugin framework.

Missing-value behavior and producer fallback are explicit upstream policies, not
hidden template helpers. Timestamp presentation uses an explicit fixed format and
timezone, with UTC as the initial default. Once formed, a payload is reused as
bytes; a delivery retry does not re-render it under a new locale, clock, or template.
Exact YAML template syntax remains a configuration contract.

JSON escaping does not provide destination-specific markup, mention, or link
safety. A supported destination profile must declare and verify its text/markup
behavior and the necessary escaping or mention controls. Generic webhook support
alone promises correct JSON encoding, not neutralization of every receiver's
markup rules. Pachca-specific payload and formatting behavior require public API
evidence and synthetic conformance tests, not assumptions from generic JSON.
If a required profile safety property cannot be established, reject that profile
or message shape instead of silently enabling richer interpretation.

## Durable assignments and failures

The stable delivery key is the tagged origin identity plus logical destination
ID. Attempts, renderer revisions, queue state, and backoff do not create a new
delivery. Within retained identity protection, replay reuses the existing routing
decision and assignment instead of selecting destinations again.

Processing atomically saves the finalized event/notice decision with every
selected assignment and its formed payload or explicit failure disposition. An
intentional no-destination decision is also durable. There is no independent
volatile routing queue or network request in this transaction.

A bad template/profile or full automatic queue for one selected destination does
not discard jobs for healthy destinations. Preserve the affected assignment as
formation-failed or undelivered-capacity work. Admission/capacity checks and their
outcomes must be consistent with the common durable transition.

Global storage exhaustion stops the transition that cannot be saved. If input
acceptance is still pending, progress cannot advance. If a candidate's source
record was already durably accepted, retain its existing pending obligation and
committed progress: do not roll progress back or pretend the earlier acknowledgement
never occurred. Other work proceeds only while it can record its own transitions
safely. Lightweight failure dispositions still consume finite storage.

Changing a template, enabling error opt-in, or adding a destination affects newly
admitted work only unless an explicit reprocessing operation says otherwise.
Requeue of a formed payload differs from explicit repair/re-formation of a failed
assignment. Neither silently mutates a payload that may already have been sent.
The detailed operator operation and retention contracts remain with delivery/state
design.

## Bounded error reporting and loop prevention

Notification eligibility comes from a stable durable owner case, not each retry,
repeated log line, or routing tick. Updating the same case does not mint new notice
identities after a time window expires. The owner, not routing, establishes when
a genuinely new failure episode exists.

Propose at most six newly admitted error notices per destination in a rolling
hour, plus at least ten minutes between admissions. The first eligible notice can
be immediate; idle time does not accumulate a burst. The quota applies to error
notice admission, not every HTTP retry or business notification.

Consume quota with the durable admission decision, including a selected notice
that ends in formation/capacity failure. Transaction rollback does not consume
it; restart does not restore it. Reattempting an already admitted notice does not
spend another admission slot. Delivery's own rate/concurrency limits separately
bound physical network work.

Repeated eligible errors can update bounded diagnostic/coalescing counts keyed
by declared kind/component/input/rule/error class/destination. They do not create
one queued notification per error or a delayed batch/digest. Already formed jobs
retain their original payload and count snapshot; live diagnostic counts never
rewrite them. Quota suppression is an explicit observable disposition, not a
successful delivery. Underlying failures remain available for inspection and
metrics regardless of secondary notification suppression.

A business-delivery failure may produce a curated notice through an eligible
system destination other than the failed logical destination. Failure to form or
deliver an error/system notice produces logs and metrics only, never another
notice about that notice. Preserve this origin/depth qualification through durable
state and restarts. There are no automatic fallback receivers.

That internal depth rule does not stop external feedback by itself. Input/rule
owners must exclude Vestrelix's own diagnostic/notification activity or preserve
sufficient verified origin information to prevent its re-detection as new business
or error cases. A source/profile path without a demonstrated exclusion must not
claim loop safety. Future adapters that make this relevant require their own
verified feedback policy; no synchronous change to the observed service is
introduced here. External metrics/alerts remain available when no system delivery
path is functional.

## Proposed limits

The following additional defaults are **proposed, not approved or benchmarked**:

| Setting | Initial proposal |
| --- | --- |
| Configured destinations | 16 |
| Configured routes | 64 |
| Initial assignments per origin | 16 |
| Final encoded JSON payload | 64 KiB |
| JSON depth / structure nodes | 8 / 256 |
| String-template source | 16 KiB per job |
| Scalar interpolations | 64 per job |
| New error notices per destination | Six per rolling hour, at least ten minutes apart |

Exhaustion gives an explicit failure/suppression/capacity outcome, never silent
clipping. The final byte limit includes JSON escaping expansion. Bound input
values, structural construction, interpolation, and encoder scratch allocations;
a limited output writer alone is insufficient if an encoder builds an oversized
buffer before writing. Reserve shared processing memory before formation and
release it after handoff; do not construct an unbounded list of payloads in RAM.
Sixteen maximum-sized payloads are about one MiB of content per origin, not an
RSS guarantee or permission to admit unlimited origins. Global database and job
retention limits remain separate requirements.

## Proposed test criteria

- Projection precedes rendering; templates cannot access raw records, forbidden
  event fields, credentials, metadata objects, or undeclared references.
- Ordinary error opt-in and system designation are independent and disabled by
  default; missing/ambiguous business audience cannot widen disclosure.
- Multiple matching routes select one assignment per origin/destination; conflicts,
  invalid conditions, and intentional no-destination outcomes remain distinct.
- Effective-value fallback retains semantic qualification; null envelope sender
  and the first scenario's envelope-only requirements are preserved.
- JSON values, destination markup/mentions, malformed fields, forbidden template
  syntax, output expansion, depth, and structure limits have explicit safe outcomes.
- Source replay, parser/template changes, and late event-ID assignment preserve
  applicable snapshots; candidate merges cannot union audiences or select latest
  incompatible definitions.
- Retried jobs reuse identical bytes and binding identity. Changed targets, missing
  definitions, and unverifiable credential/recipient rotation visibly pause work.
- Real temporary SQLite integration covers quota rollback/restart, event/assignment
  atomicity, partial destination failure, global capacity, and already-acknowledged
  candidate finalization without progress rollback.
- Admission pacing/caps, persistent case identity, immutable count snapshots,
  coalescing, and suppression cannot create a retry/notification storm.
- Errors about error-notice formation/delivery cannot recurse, and simulated
  external notification logs cannot re-enter as new qualifying cases.

Use synthetic fixtures and controlled time. These are proposed criteria, not
implemented tests, verified destination behavior, or permission to send live data.
