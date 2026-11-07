# Delivery and HTTP

**Status: approved block contract. Not implemented or transport/profile-conformance-verified.**

This block turns durable, formed assignments into bounded network attempts and
visible outcomes. The project owner approved its ownership, HTTP policy, queue
waiting, recovery, explicit requeue, limits, and test criteria. Approval does not
establish transport/profile conformance, close configuration/state gates, or
authorize implementation. No application, command syntax, Go interface, SQL
schema, or implementation sequence is specified here.

## Boundaries and identity

Input is a retained assignment with immutable profile-owned prepared content,
tagged origin identity, logical destination, authorized binding revision, and
recoverable applicable definitions. Delivery does not query sources, re-run
detection/routing, expand field permissions, or re-render a message.

The delivery identity remains origin plus logical destination, as defined by
[routing](routing-and-formatting.md). A retry round and an attempt each have their
own identity; neither creates a new event or delivery. A round is one explicitly
admitted finite automatic budget. Initial admission starts the first round;
explicit operator requeue can admit another round of the same retained delivery.

| Logical state | Meaning |
| --- | --- |
| Ready | A formed job has queue capacity and may compete for a first attempt |
| In flight | One durably charged attempt has exclusive ownership |
| Retry wait | A retry is scheduled, subject to time, capacity, rate, and cooldown constraints |
| Paused | An explicit binding, clock, or operational gate prevents sending; time budgets do not stop |
| Successful | The profile-defined acknowledgment was observed and durably recorded |
| Undelivered | Automatic work stopped with a retained reason; no success is claimed |

Undelivered reasons distinguish permanent rejection, attempt/time exhaustion,
first-start expiry, capacity, and an unsatisfied server delay. Formation failure
is an upstream disposition without sendable content, not a network attempt.
The current state and latest known attempt result are separate: an earlier
failure must not hide a later unresolved/ambiguous send.

Terminal automatic work releases runnable-queue capacity, not its retained
assignment, payload, or inspection obligation. Successful jobs never re-enter
automatic delivery because configuration changed or input was replayed.

## Attempt ownership and durable transitions

Use one owner per job and one active round. A conditional transition checks
the expected state/revision and installs a unique round/attempt token. This
coordinates workers inside the single active process; it does not replace the
process-control gate that prevents two active instances using the same state.

Before charging an attempt, obtain bounded execution/rate capacity, validate the
retained target binding and profile, and check time/cooldown eligibility. Do not
claim a large backlog and leave charged attempts waiting for a semaphore. An
unavailable/revoked binding pauses work without spending attempts or selecting a
different audience. It does not grant a fresh deadline.

Attempt start, its incremented counter, ownership, and effective request deadline
commit before any POST. No transaction stays open during network I/O. Even a
crash before the first byte can consume this attempt. There are no automatic
refunds based on a best-effort claim that a receiver saw nothing.

The outcome transition checks the same token and revision, then saves success,
terminal non-delivery, or the next eligible retry time. A stale completion cannot
overwrite a newer round or owner. If start commit is uncertain, do not send on an
assumption that it succeeded. If outcome commit fails, do not immediately send
again: resolve durable state and retain exclusive ownership first. A confirmed
commit can be recognized without issuing another POST; an unrecorded response
cannot be recovered by inventing success.

Cancellation does not itself release physical ownership. Retain execution slots
and prevent replacement sends until the network worker has actually stopped or
the process has terminated. Conditional result writes alone do not stop a stale
worker from writing request bytes. Local persistence failure can therefore stall
delivery; global storage failure does not permit unrecorded network work.

## Queue time, retry budgets, and clocks

Use a one-hour first-start deadline from admission of a round. For the initial
round this is job admission; explicit requeue records a new round admission
without changing the original job admission. This deadline applies only until
the first charged attempt. Expiry leaves visible first-start non-delivery with
zero attempts; it does not quietly discard a queued message.

The first charged attempt starts the already approved one-hour retry budget:

- At most eleven charged attempts: the initial attempt and ten retries.
- Each request has at most 15 seconds, shortened by remaining round time.
- Retry delays start at 15 seconds and double per retry; apply a uniformly sampled
  multiplier from 0.9 to 1.1, then cap the randomized delay at ten minutes.
- Sample a delay once for the transition and persist its next-eligible time.
  Restart does not resample toward an earlier retry or restore a counter.
- Rate/queue waits, pauses, outages, and network time after the first charge all
  count against the same round deadline. No attempt starts at/after it.

Ordinary retry backoff is measured from completion of the failed attempt. Recovery
of an interrupted attempt establishes a conservative new wait at recovery, still
inside the original deadline; it never creates a new hour. Success observed within
the request deadline may be committed later; a late durable write alone does not
turn that observation into another send. Do not accept a response first observed
after the request deadline as a timely acknowledgment.

Use monotonic elapsed time for live-process durations and retain UTC anchors for
restart. Retain durable clock high-water evidence and explicitly pause fail-closed
on a detected backward wall-clock jump, not a frozen clock that stretches budgets.
Forward jumps can expire work early. A pause never shortens a retained server
cooldown or automatically resets a round; resume requires validated clock/budget
recovery. Arbitrary clock corrections while the process is stopped cannot always
be detected without trusted external time. Cross-restart wall-clock guarantees
therefore require a sufficiently correct host clock; this design introduces no
external time service and claims no protection against every clock fault.

Expired work cannot send merely because it was paused. Expiring its round also
does not clear a destination-wide safety/cooldown gate.

## HTTP exchange and target safety

Use HTTPS POST with normal certificate/hostname verification for production.
There is no insecure-TLS fallback, alternate recipient, automatic authentication
discovery, or cookie jar. Tests may use local plain-HTTP synthetic servers; this
does not make arbitrary production HTTP targets supported.

Disable all automatic redirects, including same-origin redirects. A 3xx is a
visible endpoint/profile failure, not permission to forward a payload or secrets
to `Location`. Do not inherit environment proxies; any supported trusted proxy
requires explicit configuration and privacy review. Target and credential
references must satisfy the approved binding-continuity contract at every send.

The required accounting property is at most one outbound POST exchange per
charged attempt. Go's standard transport can retry some requests, particularly
replayable requests carrying idempotency headers; absence of a retry wrapper is
not sufficient. Use this conservative initial candidate configuration:

- HTTP/1.1 only, fresh connection per attempt, no keep-alive reuse.
- A non-replayable request body, without an automatic body-recreation hook.
- No redirect/retry wrapper, automatic protocol fallback that replays a POST, or
  TLS early-data application replay.

These are candidate standard-library settings, not a conformance claim. Before
supporting a Go/transport configuration, synthetic tests must establish the
property under resets, partial writes, idempotency headers, and attempted reuse.
Count outbound request bytes as well as completed server-side requests. Multiple
address connection attempts or TLS handshake packets are not additional POSTs;
receiver/proxy-internal behavior is outside this boundary. If the standard
transport cannot satisfy the property, return to architectural review rather than
silently building a custom HTTP/TLS stack or allowing uncharged resends.

The request deadline covers connection acquisition, DNS/dialing, TLS, writing,
headers, and any required acknowledgment body. Limit response headers and body
input to 16 KiB and 64 KiB respectively, with bounded profile parsing and memory. Disable
implicit compression/decompression; reject unsupported content encoding when a
body is required. Close bodies/connections without unbounded draining. Do not
follow response links or fetch acknowledgment URLs.

## Acknowledgment and error classification

A profile defines its success predicate before it is enabled. Use an explicit
generic JSON webhook profile whose predicate is a valid final HTTP 2xx status;
its response body is irrelevant. In that profile, confirmed 202 means accepted
by the endpoint, not completed downstream processing, read receipt, or inbox
placement. Once those successful headers are observed, an irrelevant body read
failure or size excess does not cause another send.

A profile requiring an application acknowledgment must validate it within the
response/time limits. Missing, truncated, malformed, or contradictory required
acknowledgment after a possible send is ambiguous and retried within the remaining
budget. A documented negative acknowledgment follows the profile's closed
classification. An unknown profile contract blocks activation before any send;
do not discover after sending that no success/error policy exists.

| Result | Generic behavior |
| --- | --- |
| Valid profile-defined success | Save success; no more automatic attempts |
| Timeout, reset, interrupted response, transient connection/DNS failure | Retry within budget; preserve ambiguity where acceptance is unknown |
| HTTP 408, 429, or 5xx except 501/505 | Retry within budget and applicable server delay |
| HTTP 3xx, other 4xx, 501/505 | Stop automatic work with a visible permanent endpoint/request reason |
| Invalid target/request, invalid certificate/hostname, unsupported protocol | Stop or pause for operator/configuration repair; no repeated transient sequence |
| Invalid required application acknowledgment | Ambiguous retry, not success and not a guessed negative acknowledgment |

A profile can refine documented application outcomes through a reviewed bounded
mapping. HTTP 409 is not automatically proof of an idempotent duplicate. Unknown
transport outcomes after possible writing favor possible duplicate delivery;
typed permanent configuration failures do not consume ten futile retries.
Classification records what is known, not a claim that every failed response
proves the receiver had no side effect.

Pachca remains the first intended profile, not a verified one. Its exact payload,
success predicate, application error mapping, text/mention behavior, and any
idempotency support require public API evidence and synthetic conformance tests.
Do not infer them from the generic profile or test by sending live notifications.

Use a destination-supported idempotency key only under its documented contract.
Derive it from the stable delivery identity, not an attempt or manual round; avoid
exposing event fields through it. Do not assume the receiver retains keys as long
as Vestrelix retains jobs. Identical prepared bytes and keys reduce duplicates
only when the receiver actually honors them; neither establishes exactly once.

## Retry-After and destination cooldown

Honor `Retry-After` on generic HTTP 429 and 503, or additional outcomes
explicitly defined by a verified profile. Accept one bounded value as decimal
nonnegative delay-seconds or an HTTP date. Zero and a date in the past are valid;
negative, conflicting/multiple, or malformed values produce a safe invalid-hint
reason and ordinary backoff. Do not log the raw header.

Translate a delta to an absolute not-before once at response receipt. Persist the
outcome and destination cooldown together; restart does not add the delta again.
Take the later of normal backoff and server not-before. Jitter must not move a
retry earlier than the server minimum. A newly observed hint may extend, never
shorten, an existing cooldown.

Apply a retained cooldown to the stable logical destination across jobs, rounds,
and credential revisions. Manual requeue cannot bypass it. Different logical
destinations are not automatically grouped by similar-looking secret URLs; a
provider-wide quota would need its own explicit contract.

If the required wait from the current outcome exceeds the ten-minute automatic
delay cap or cannot fit the round deadline, stop that job visibly rather than
clamp the hint into an early retry. Retain the full representable destination
not-before for other/new rounds. An otherwise valid decimal delay outside the
representable range causes an explicit destination pause, not malformed-header
fallback and a near-term send. Unrepresentable delays require reviewed operator
recovery; ordinary requeue is not an override. No hint can be retained if a crash
loses the response before persistence, so this promise concerns observed, durably
recorded hints, not unknowable server responses.

## Scheduling, capacity, and independent destinations

These additional defaults are **approved, not benchmarked**:

| Setting | Initial value |
| --- | --- |
| First-start wait per newly admitted round | One hour |
| Active network attempts per destination / process | 1 / 4 |
| Attempt-start rate per destination | One per second; burst one |
| Automatic queue per destination / process | 1,000 / 10,000 jobs |
| Response headers / body input | 16 KiB / 64 KiB |
| Graceful delivery drain | 20 seconds maximum |
| Retained attempt detail per job | Most recent 32 entries, at most 2 KiB each |

Queue capacity counts ready, retry-wait, in-flight, and paused jobs, including
manual rounds; transitions between those states do not free a slot. Reserve a
slot atomically with round admission. Terminal work frees the slot but still
consumes global storage. Queue limits are not total database/retention limits.
Even 10,000 maximum-sized webhook bodies alone approach 625 MiB; this is a bound,
not a promised acceptable footprint or a disk reservation.

A destination at capacity retains an undelivered assignment. For formed work,
retain exact prepared content directly or by a protected immutable reference so
explicit requeue can reuse it. A small failure record cannot replace bytes that
are otherwise irrecoverable. If global storage cannot save required content and
dispositions, the common durable transition fails; healthy destinations proceed
only while their own transitions remain persistable.

Schedule eligible destinations fairly, with due work ordered deterministically
by eligibility time, admission time, and stable identity. Retry waits and cooldowns
do not head-of-line block other ready jobs. Bound the state scan and loaded batch;
do not materialize every retained job or start a goroutine/timer per queued job.
Persist destination next-start evidence so restart cannot manufacture a burst;
the in-memory limiter alone is not the durable pacing contract. Source processing
does not wait synchronously for a webhook to recover.

## Restart, shutdown, and explicit operator actions

After restart, recover each open charged attempt as consumed and ambiguous once
the old process is known to be gone. Retain its original round deadline. Retry
only if attempt/time budgets, target continuity, clock state, rate, and cooldown
allow it; otherwise expose non-delivery. SQLite cannot prove whether a pre-crash
POST reached a receiver. Favor a duplicate within budget, not fabricated success.

Shutdown stops new claims first. Allow at most 20 seconds to drain delivery
workers and persist results, without extending any request deadline. Then cancel
remaining exchanges; charged interrupted work remains consumed and ambiguous.
Do not release an unfinished worker's slot to a replacement during shutdown.
A hard kill relies on the same durable recovery, not a presumed clean exit.

Use a local explicit requeue operation with a caller-supplied operation ID and
expected job revision. It admits at most one new round atomically with queue
capacity and an auditable chosen, validated delivery-policy revision. This gives
a new first-start window and, on its first charge, a new finite retry budget; it
does not erase previous counters or change payload, audience, binding identity,
delivery ID, or destination idempotency key. Use repaired compatible credentials
only under the approved target-continuity rules.

Requeue applies to retained formed undelivered jobs, not successful or in-flight
jobs. A paused live round can resume only under its existing budget and resolved
gate; it cannot obtain a new hour by toggling pause. Formation failure requires a
separately specified repair/re-formation action, not send-time reconstruction.
If admission fails, no new round/budget is created. Error-notice routing admission
quota is not charged again; network rate limits and server cooldowns still apply.

Deduplicate operation IDs and reject stale revisions while their protection
markers are retained. Diagnostic history eviction must not erase those markers
or let an old command issue another budget. The approved
[state lifecycle contract](sqlite-state-lifecycle.md#businessterminal-identity-and-manual-operation-protection)
defines bounded operation protection, minimum identity retention, and job expiry.
Concrete safe-retirement/post-expiry evidence remains a
[gate](open-decisions.md#configuration-and-state-compatibility), not a promise of
unlimited history or perpetual idempotency. Do not enable requeue without validated
protection/retention behavior. Warn that another round
may duplicate a previously accepted notification, especially after ambiguous
outcomes or expiration of the receiver's idempotency protection. There is no
automatic periodic requeue, bulk history replay, or force-send bypass here.

## Private diagnostics and error reporting

Reuse the exact retained prepared content through the approved protected local
inspection surface. Ordinary logs/notices/default inspection expose safe typed
metadata only: phase/class, HTTP status, timing, byte counts, ambiguity, applicable
revisions, counters, and opaque diagnostic reference. Never serialize arbitrary
HTTP errors, target URLs, headers, bodies, or credentials into ordinary output.

Retain at most the latest 32 bounded attempt detail entries per job,
plus bounded lifetime counters and latest known result/current unresolved status.
Eviction is explicit, with omitted-entry counts; it cannot remove pending
ownership, budget, round numbering, operation markers, or delivery identity.
These limits bound attempt detail only, not total job/audit storage. The state
contract must bound that storage without silently losing active obligations.

Read response content in bounded memory only when needed for profile semantics.
Persist no raw response/header bodies by default, even for local debugging: a
receiver can echo payloads, secret URLs, or credentials. A profile may map known
response codes to a closed safe enum; an arbitrary server string is not safe
because its field name was allowlisted. Preserve a safe parse/error path and size
reason, not the offending value. Rich response capture would need another explicit
privacy/retention decision; regex redaction is not a guarantee of safety.

Prepared content is not a complete wire capture or evidence of receiver display.
Apply the approved error/system notice audience, quota, and loop rules to stable
delivery failure cases, not every attempt. An error/system notice's own delivery
failure produces logs/metrics only, never another notice. Terminal work stays
inspectable even if its secondary notice is suppressed.

## Test criteria and evidence gates

- Real temporary SQLite tests and controlled clocks cover concurrent claims,
  token-conditional results, uncertain commits, and crash barriers before charge,
  after charge, after receiver acceptance, and before result commit.
- Interrupted sends consume attempts; restart, pause, clock jumps, and requeue
  cannot silently reset the same round. Separate first-start/retry deadlines,
  persisted jitter, request timeout, and both exhaustion causes remain observable.
- Synthetic HTTP/TLS peers verify no redirect, environment-proxy leak, credential
  forwarding, hidden POST replay, or post-cancellation overlapping sender. Examine
  partial request bytes, not just successfully parsed requests.
- Generic 2xx/202, irrelevant bodies, required application acknowledgments, 409,
  negative acknowledgments, certificate failures, response limits/encoding, and
  permanent/transient mappings have distinct tested outcomes.
- `Retry-After` covers zero/past dates, delta/date values, malformed/multiple input,
  huge decimal overflow, cooldown extension, restart, deadlines, and long hints.
  Another job or manual round cannot bypass a retained destination cooldown.
- A failed/paused/full destination does not monopolize others. Queue accounting,
  bounded scans, fair scheduling, start pacing, capacity failure with retained
  prepared bytes, and global storage failure preserve the durable contract.
- Graceful and forced shutdown never release physical ownership to a competing
  send; late/stale completion cannot overwrite durable state or reopen success.
- Requeue is explicit, operation-idempotent within its protection horizon, and
  revision-checked. It preserves bytes/audience/identity, cannot requeue successful
  work, and does not erase audit markers when diagnostic details are evicted.
- Receiver-echoed secrets/PII and arbitrary error text cannot enter persisted
  response diagnostics, ordinary logs, metrics, or system notices. Local prepared
  content inspection remains read-only and does not claim wire/receipt proof.

These are approved acceptance criteria, not implemented tests or verified
destination/transport behavior. Configuration recovery, state retention/capacity,
single-instance enforcement, and profile conformance remain explicit prerequisites.

## Public references

- [Go HTTP client behavior](https://pkg.go.dev/net/http#Client.Do)
- [Go HTTP transport retry behavior](https://pkg.go.dev/net/http#Transport)
- [HTTP Retry-After semantics, RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3)
- [HTTP 429, RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html#section-4)

These sources describe protocol/library behavior, not Pachca conformance or a
guarantee that the candidate transport settings satisfy this contract.
