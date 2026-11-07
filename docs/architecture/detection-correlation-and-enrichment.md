# Detection, correlation, and enrichment

**Status: approved block contract. Not implemented or source-proof-verified.**

This block combines normalized observations into operation context and qualifying
business events. The project owner approved its lifecycle proof requirements,
occurrence identity, bounded waiting, enrichment, and resource policies. Approval
does not establish source-generation proof, close explicitly open contracts, or
authorize implementation.

## Responsibility and contracts

Input consists of typed observations with field quality and semantic provenance,
stable source/correlation namespaces, applicable rule/profile revisions, and
coverage information from ingestion. Source search time, relay receipt time,
failure event time, and first detection time remain distinct.

| Output | Meaning |
| --- | --- |
| No matching event | Known observations do not satisfy a rule; no invented failure |
| Minimal operation context | Facts potentially needed by a later event, qualified by lifecycle evidence |
| Candidate and pending work | A possible occurrence awaiting identity, coverage, or required context |
| Context request | A bounded logical need bound by processing to a configured source lookup |
| Normalized event | A proven occurrence with required valid facts and stable identity, before destination formatting |
| Explicit unresolved outcome | Ambiguity, incompatibility, missing context, expiry, or resource exhaustion prevents safe completion |

Detection owns rule conditions, correlation meaning, event occurrence identity,
and enrichment decisions. Processing coordinates concurrency and durable
transitions. Source adapters execute source-specific lookups; routing chooses
audiences and permitted payloads; delivery owns network attempts. There is no SQL,
LogsQL, destination payload format, or network retry loop inside portable rules.

Rule conditions are bounded declarative checks over declared typed facts. This
does not select an expression library or create a general-purpose rule language.

## Correlation and lifecycle proof

An operation is not a queue ID. The mail profile requires an originating relay
namespace, queue ID, and an authoritative generation anchor. The profile must
identify which receipt/start evidence establishes that anchor. Repeated queue
activation, a Message-ID, a process restart, or the latest matching timestamp does
not independently establish a new message lifecycle.

Facts about different relays or generations remain separate. Before an anchor is
proven, retain bounded unresolved evidence rather than attaching it to the nearest
existing operation. Conflicting or simultaneous start evidence is not resolved by
arbitrary sorting. Removal is an observed lifecycle marker, not proof that every
recipient failed; requeue/hold behavior needs an explicit supported interpretation.

For the initial contract, each rule/correlation namespace has one owning input.
Reject overlapping ownership that lacks a proven compatible anchor/view contract.
The input ID is not a business occurrence key. Ownership transfer needs an explicit
state-compatibility decision, not a new namespace that resends events.

### Late evidence and the finalization gate

Discovery can create context and candidates immediately. For reusable queue IDs,
the initial mail profile must not finalize by assuming that the only generation
currently visible is the right one. A late start record could otherwise associate
a rejection with another message's sender or subject.

Require a profile-specific proof contract before final binding:

1. Declare authoritative start, result, and relevant boundary evidence and ensure
   the input selection includes all required record classes for the source scope.
2. Establish how these records' source search-time coordinates bound every
   potentially competing generation, including clock uncertainty and reordering.
3. Require complete settled coverage of those declared intervals, or equivalent
   verified source evidence, and exactly one compatible generation membership.
4. Reject incompatible, incomplete, or ambiguous evidence instead of inventing a
   connection. A complete history lookup alone does not prove that late evidence
   cannot still arrive.

Passing the settlement frontier through the result timestamp is not sufficient
by itself. With ingestion-time search coordinates, a competing start record may
have a later search timestamp than the result. The profile must prove the required
coverage horizon; an unknown/unbounded relationship leaves the candidate unresolved
even after an hour has elapsed. Establishing the exact supported proof contract
is an acceptance gate, not a fact demonstrated by this design.

This gate does not change ingestion's discovery/settlement protocol. It trades
notification latency for avoiding incorrect cross-message disclosure. A different
profile with a proven stable operation identity can define a less restrictive
gate. No arbitrary profile receives that guarantee automatically.

Observation start and available history also bound the proof. An operation whose
required start predates supported observation/backfill cannot be connected merely
because one queue ID is visible now. No finite sample or successful empty query
proves that missing source history never existed.

## Observation and notification boundaries

Configure the source observation/context-loading start separately from the earliest
eligible business-event time. The first boundary belongs to ingestion's source
search coordinate; the second is an inclusive cutoff on validated business-event
time. For the mail scenario, use the qualifying final recipient failure time, not
relay receipt, observation, or detection time. Missing or invalid required failure
time cannot be replaced by any of those other clocks.

Earlier observations may supply receipt/context and lifecycle evidence for an
eligible later failure. A failure before the cutoff does not create a business
event or delivery assignment merely because it was discovered later. Operational
and processing-error reporting remain governed by their separate policies.

The operator chooses both boundaries explicitly; no automatic seven-day backfill
or pre-observation coverage is implied. Earlier context is useful only while it
passes ordinary retention, quality, and lifecycle requirements. Restart preserves
the boundaries and committed progress. Changing either boundary requires an
explicit supported compatibility/replay decision, not a silent historical resend
or reinterpretation of already admitted work.

Catch-up after an outage may discover an eligible failure long after it occurred.
Age alone does not suppress its notification, but available context, lifecycle
proof, normal admission limits, and deadlines still apply. Existing terminal work
is not revived, and receipt-anchored context expiry is not extended to make an old
event complete.

## First mail rule and event identity

The first rule requires all of the following for a particular recipient:

- The actual SMTP envelope recipient domain matches the configured allowlist.
- Valid, attributable delivery-result evidence establishes final failure for that
  recipient, not just a message-wide marker.
- The result contains explicit permanent rejection from the remote SMTP server.
- Lifecycle membership passes the proof gate, and required message fields are
  valid or obtained through an allowed same-meaning fallback.

`status=bounced` alone, a local failure, temporary deferral, timeout, DNS/configuration
error, or queue expiry without remote rejection does not qualify. Do not infer
failure for other recipients. A proven recipient-specific final result need not
wait for every recipient to finish or for removal, except where a boundary marker
is necessary to prove generation membership.

Initially support ASCII envelope addresses, including ASCII punycode domain
representations. Unicode local parts and Unicode-form domain names are explicitly
unsupported, not silently converted, transliterated, or treated as a nonmatch.
This selects an address scope, not a complete address-parser/source-format
contract or a new IDNA normalization algorithm. Subject charset support is
independent; non-ASCII subjects are not excluded by this address policy.

Use exact domain matching by default, comparing normalized ASCII domain
labels without case sensitivity. Subdomain inclusion is an explicit option and
uses label boundaries, not substring/suffix matching. Preserve local-part case and
content; do not strip plus tags. The valid SMTP null reverse path remains present
sender context, not an unsupported or missing address.

The mail occurrence key is the stable rule ID, proven operation generation,
rejected recipient key, and event kind. It represents one permanent-remote-rejection
event per recipient/rule/generation. Repeated diagnostics and different source
records establishing that same fact do not create new occurrences. Other
recipients, rules, and genuinely different event kinds remain distinct.

Persist a stable event identity for that occurrence. Rule descriptions, compatible
configuration/profile/template revisions, detection time, and network attempts do
not enter its identity. Record fingerprints, provisional work IDs, correlation
identity, event identity, and destination-specific delivery identity are not
interchangeable.

The normalized event carries validated envelope sender, rejected envelope recipient,
decoded subject, relay receipt timestamp, failure event time, detection time,
necessary evidence qualifications, and applicable revisions. Routing exposes only
the permitted fields for a destination; the mail notification remains limited to
the four fields in functional scope.

The SMTP null reverse path is valid envelope context. An opt-in effective sender
chosen from header `From:` retains that meaning and cannot silently satisfy this
envelope-only rule. A header-based notification variant needs explicit different
requirements and labeling.

## Context, candidates, and durable transitions

Receipt/context observations can create minimal operation state before a failure
is known. Keep only required sender, subject, receipt time, selected evidence
references, and lifecycle/provenance qualifications. Unresolved evidence is not
merged across possible generations. Do not persist raw logs, full SMTP diagnostics,
bodies, attachments, or a list of unrelated recipients as a convenience.

Validate cross-record consistency within a proven generation as well as each
observation's quality. Independently valid but incompatible sender, subject,
receipt-time, or other required facts retain an explicit conflict qualification;
do not resolve them through silent last-write-wins or arrival order. Affected
fields cannot satisfy finalization until supported profile semantics resolve the
contradiction with preserved provenance. If that is impossible within budget,
completion remains unresolved.

Preserving context before the future recipient is known has a privacy/storage
cost: configured source scopes must be narrow, and retention/capacity applies to
all admitted context, not only messages that eventually trigger notifications.

| Candidate condition | Required behavior |
| --- | --- |
| Awaiting lifecycle/coverage | Retain the proof obligation; no guessed message binding |
| Awaiting context | Keep bounded enrichment work and its original deadlines |
| Ready | Identity, conditions, and required facts are valid; request atomic finalization |
| Finalized | Reuse the existing occurrence/event; do not create deliveries again |
| Not applicable | Record that the conditions do not qualify without a business-failure notification |
| Unresolved terminal | Retain a safe reason and bounded inspection/reprocessing information; do not claim a complete event |

Processing commits record replay protection with context/candidate changes,
follow-up obligations, or explicit unsupported/failure outcomes before advancing
input progress. Shared read-decide-write transitions must serialize or validate
their starting state; atomic writes alone do not prevent lost context updates.

Finalization uses the approved event-plus-routing/delivery boundary: event and
delivery assignments, or an explicit durable formation failure, commit together.
No network operation is inside that transaction. Crash recovery cannot leave an
accepted event with a forgotten delivery obligation.

### Provisional duplicates and terminal work

Before lifecycle identity is proven, only identical evidence work can be reliably
deduplicated by stable rule/source evidence references. Semantically duplicate
candidates may coexist temporarily within resource caps. Their provisional IDs
are not business event IDs.

When candidates are proven to represent one occurrence, merge without extending
work: preserve the earliest original deadline and account for already consumed
lookup/retry work across all merged candidates. New evidence fingerprints, source
replay, and revision changes do not create a fresh budget for the same occurrence.

Check retained finalized and terminal qualifications before finalization. An
already finalized occurrence remains finalized without new jobs. If no event has
been finalized and equivalent work has a terminal outcome, new evidence does not
silently resurrect it: explicit reprocessing is required. If a new candidate
cannot be distinguished safely from retained terminal work, pause/unresolve rather
than assume a new occurrence. This protection is bounded by the documented
retention of event/terminal identity metadata, not an unlimited history claim.

## Bounded enrichment and waiting

Use a three-hour total candidate deadline from its first durable detection,
including maturity waiting, source pauses, and context lookups. New facts and
restarts do not refresh it. This is separate from each source acquisition's
one-hour retry budget and the delivery budget of a later webhook job.

Expiry is an unresolved processing outcome, not proof of a mail failure or success.
An outage or incomplete coverage never becomes a business rejection. Later data
does not automatically revive terminal work. Operator inspection and explicit
reprocessing remain possible under the state/retention contract.

Lookup policy:

1. Consult compatible minimal durable context first.
2. Express a logical context need through the configured processing binding, not
   LogsQL inside the rule. Source-specific parameters are validated and escaped.
3. Use bounded targeted windows anchored in trustworthy available evidence. Keep
   the approved five-minute request interval, row/byte/time limits, and shared
   source concurrency/buffer budgets. Do not silently widen to a seven-day query.
4. Use at most eight lookup rounds and 32 physical requests per candidate,
   including subdivisions and transport retries. Candidate merging preserves the
   aggregate consumed work. A successful empty response means no matching context
   was found then, not that the source failed or the context never existed.
5. Incomplete responses do not prove absence. Each logical acquisition persists
   its source retry/deadline state; the candidate's three-hour deadline and total
   lookup cap also apply. A scheduled probe cannot replenish those budgets.

History results return through compatible extraction to the requester. They do
not advance polling frontiers or trigger unrelated rules. History evidence also
must satisfy the generation/maturity proof rather than bypass it.

Targeted recovery is not an exhaustive search of arbitrary history. If required
start/context lies outside known lookup ranges, supported observation or explicit
backfill must provide it; otherwise completion can remain unresolved within budget.

## Retention, revisions, and late changes

Seven days of minimal context retention is agreed. Use its ordinary expiry
anchor as validated relay receipt time, without extending it through source replay
or deferred activity. This anchor and the following dependency policy have separate
block approval; they are not implied merely by selecting a seven-day duration.

Distinguish retention from guarantee scope. Guarantee correlation only
where required context and lifecycle proof remain available under the declared
observation/history contract. After ordinary context expiry, bounded history
recovery may still succeed; expiry alone does not prove that recovery is impossible.
Arbitrarily long hold/requeue operations have no unconditional guarantee.

An already admitted candidate may pin only the minimal snapshot it needs until
its fixed three-hour deadline; expiry then becomes an explicit unresolved outcome
if necessary. Do not silently delete its obligation at the ordinary context TTL.
Finalized events, delivery payloads/jobs, and replay/terminal identity protection
have separate retention obligations. None is deleted merely because reusable mail
context expired. Cleanup and capacity must account for pinned data.

Pending work retains applicable rule/profile/configuration semantics, not merely
revision numbers. If restart cannot recover the required definition, or new facts
were extracted under unproven incompatible semantics, pause the work visibly rather
than evaluate it using whichever configuration is current. The mechanism for
recoverable definitions belongs to configuration/state design.

Finalized event facts are immutable. Contradictory or out-of-contract late evidence
is exposed safely, not used to silently rewrite a sent notification, invent a
new occurrence, or resend history. Any correction/reprocessing behavior needs an
explicit operator action and its own contract.

## Resource limits and observability

The following defaults are **approved, not benchmarked**:

| Setting | Initial value |
| --- | --- |
| Ordinary operation contexts | 10,000 globally |
| Pending candidates | 1,000 globally |
| Minimal content per context/candidate | 32 KiB |
| Selected evidence references per context | 64 |
| Combined context/candidate content allocation | 256 MiB, independently of count limits |
| Candidate wait | Three hours from first durable detection |
| Context lookup work | Eight rounds and 32 requests per candidate |
| Due candidate evaluations per scheduler turn | 100 |

Count and byte limits both apply: all contexts cannot simultaneously grow to the
per-context maximum merely because the count cap permits it. The content budget
is not a bound on SQLite file size, indexes, event/jobs storage, or process RSS.
The approved [state lifecycle contract](sqlite-state-lifecycle.md) defines finite
global database/capacity policy; resource/page-amplification evidence remains
outstanding. Do not load the entire durable context store into memory; transient
evaluation also respects the shared ingestion/processing allocation budget.

Keep decisive/ambiguity evidence rather than an ever-growing observation history.
If retaining safe proof exceeds a limit, expose unresolved/capacity work or pause
admission; do not evict evidence silently and guess. A context/candidate cap pauses
affected admission without acknowledging lost work. Other accepted work proceeds
only within the remaining shared capacity; global limits cannot promise unlimited
destination or input independence.

Expose candidate age/count, unresolved reasons, lookup work, conflicts, expiry,
and capacity failures with bounded rule/input/error-class labels. Diagnostics and
error/system notifications must not contain subjects, addresses, raw diagnostics,
secret URLs, or sensitive identifiers by default. This block emits safe outcomes;
routing/operations determines permitted notification audiences and repetition.

## Preliminary source feasibility

An authorized, bounded, read-only inspection of a non-public source found
subject-bearing cleanup records, envelope context, receipt evidence, and
recipient delivery results. The sampled results included bounced outcomes both
with and without explicit remote 5xx evidence; only the qualifying attributable
remote rejection can satisfy the first rule.

The inspection also found original and structured representations consistent with
the same underlying observations. Representation differences may correctly yield
different source fingerprints; this does not authorize duplicate business events
or prove semantic deduplication. Concrete mappings and compatible lifecycle proof
still need a supported profile contract.

These are deployment-specific feasibility observations, not universal Postfix
defaults or acceptance evidence. They do not establish complete source selection,
unambiguous queue-ID generations, absence of subject truncation, all supported
formats/charsets, or availability throughout the retention horizon. Do not derive
required guarantees from a finite sample. No operational values, raw records,
connection details, exact sampling dates/counts, or private fixtures accompany
this note; public tests must use independently written synthetic cases.

### Public upstream constraints, not deployment conclusions

The Postfix `postqueue(1)` documentation explicitly permits queue-ID reuse unless
long IDs are enabled and time is monotonic; even then, IDs are not globally unique
across Postfix instances. A hostname label alone is not evidence that a selected
source contains only one independently managed queue. The profile must establish
the originating-instance namespace and its authoritative start/coverage contract;
neither short nor long ID syntax bypasses that gate.

In the pinned upstream `cleanup_message.c` logging path, `cleanup_act_log`
formats the matched header/body content using `%.200s` before appending context.
This bound concerns that action-logging path, not every possible subject producer
or every deployed version. It can discard a subject suffix without an explicit
ellipsis, including part of an encoded word. A complete JSON record and closing
log-context trailer therefore do not prove a complete subject.

A supported source/profile must establish the selected producer's bounds and
transformations. Values reaching a known content limit are potentially truncated
even when syntactically decodable; classify them explicitly unless independent
complete same-meaning evidence resolves the issue. Do not guess lost suffixes or
silently relax the required decoded subject. Installed version, logging actions,
collector transformations, and instance provenance still need deployment evidence;
these public observations do not establish truncation or a defect in an inspected
deployment.

Postfix also documents `nested_header_checks` as inheriting `header_checks` by
default and inspecting headers of attached messages. In the pinned header callback,
primary, MIME, and nested checks all invoke the same `header` action context.
Consequently, an `INFO` Subject record need not identify header depth unless its
producer/action has an independently verified distinguishing contract. This does
not make every INFO producer unsupported: an explicitly proven primary-only
producer or other trusted discriminator can satisfy the requirement.

A sole decodable Subject entry cannot prove that the outer message had that
Subject; an outer message can lack the header while an attachment supplies one.
Do not select the first, last, or only matching Subject as a workaround. Missing
primary-origin evidence is a source/profile gate under the existing prohibition
on Postfix configuration changes, not permission to forward an attachment's subject or claim
that every possible alternative source is unavailable.

## Test criteria

- Every mail condition has negative cases; local bounce, unrelated 5xx text,
  temporary failures, and expiry cannot manufacture remote rejection.
- Mixed recipient outcomes produce only qualifying recipient occurrences; domain
  labels, subdomain opt-in, local-part case, and address roles are not conflated.
- ASCII/punycode addresses remain distinct from unsupported Unicode address forms;
  no implicit conversion or missing-value fallback hides unsupported data.
- Failure times before, exactly at, and after the notification cutoff differ as
  specified, even when source/receipt/detection times differ. Earlier context can
  support eligible later failures without notifying about pre-cutoff failures.
- Restart and long-outage catch-up preserve both boundaries and existing terminal
  work/deadlines; late discovery alone does not suppress an otherwise eligible event.
- Repeated queue IDs across relays/generations, simultaneous starts, and late
  competing evidence never attach another message's sender or subject.
- Conflicting valid facts across records cannot overwrite context silently or
  satisfy required fields until the profile resolves their semantic relationship.
- Settlement through a result is not accepted as sufficient proof when source
  coordinates can put a competing start later; unknown proof remains unresolved.
- Late/out-of-order context and restart days after receipt preserve identity,
  required facts, and original candidate/acquisition budgets.
- Provisional merges sum consumed work, keep the earliest deadline, and cannot
  revive equivalent terminal work or recreate finalized events/jobs.
- Null reverse path, same-meaning fallback, and opt-in header selection retain
  semantics; header selection cannot satisfy this envelope-only mail rule.
- Complete empty lookups differ from errors/incomplete results; targeted limits,
  source pauses, three-hour expiry, and explicit reprocessing remain finite.
- Context TTL, candidate pinning, payload retention, and identity retention are
  distinct; cleanup does not silently remove pending obligations.
- Missing old rule definitions and incompatible new observations pause work;
  parser/template/configuration changes do not silently resend events.
- Real temporary SQLite integration covers interrupted transitions, shared-context
  concurrency, occurrence uniqueness, and event/routing atomicity.
- Count/byte/evidence limits and diagnostic redaction fail visibly without a raw
  log mirror, sensitive labels, or unbounded memory/timer work.

Use independently written synthetic fixtures and controlled time. These are
approved criteria, not implemented tests or verified source-generation semantics.

## Public references

- [Postfix queue identity limitations](https://www.postfix.org/postqueue.1.html)
- [Postfix long and short queue-ID formats](https://www.postfix.org/postconf.5.html#enable_long_queue_ids)
- [Postfix nested-header inspection default](https://www.postfix.org/postconf.5.html#nested_header_checks)
- [Pinned upstream cleanup action logger](https://github.com/vdukhovni/postfix/blob/108885f3c56c9246802deca3939644aba37ee697/postfix/src/cleanup/cleanup_message.c#L262-L288)
- [Pinned primary/MIME/nested header action dispatch](https://github.com/vdukhovni/postfix/blob/108885f3c56c9246802deca3939644aba37ee697/postfix/src/cleanup/cleanup_message.c#L539-L553)

Public implementation evidence describes the cited revision and path only; it
does not identify or validate a private deployment's installed software.
