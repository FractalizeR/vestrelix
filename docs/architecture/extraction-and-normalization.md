# Extraction and normalization

**Status: review-ready proposal; not approved. Not an implementation baseline.**

This block turns source fields and text into bounded, typed observations. It does
not decide that an event occurred. The approved [ingestion contract](ingestion.md)
supplies source records; detection, correlation, and enrichment consume the
resulting facts. This proposal does not approve those later blocks.

## Responsibility and boundary

The block belongs logically to `detection`, with format-specific interpretation in
profiles such as `detection/postfix`. Source transport is independent of log
format: a profile does not execute LogsQL or depend on a webhook payload.

Extraction does not read history, join records, construct queue-ID lifecycles,
assign event/delivery identities, execute SQL, route messages, or retry network
operations. It has no durable state and performs no external side effects.

Source fingerprinting happens before these transformations. Subject decoding,
field conversion, and ignoring unneeded fields cannot change input equivalence.

## Input and output contract

Input consists of a structurally accepted source record, its source view and
fingerprint, search-time coordinate, acquisition metadata, and the applicable
extraction profile/revision. Configuration supplies the fields needed by rules,
correlation, and enrichment, plus mandatory evidence needed to interpret the
record class safely.

The proposed initial representation produces at most one normalized observation
per record. It contains a declared record class, typed scalar facts, per-field
quality, safe issue codes, and provenance linking facts to their source and
profile. It is not a normalized business event or a destination message.

This is a supported-format restriction, not a universal property of source
records. A record containing multiple independent recipient/results that cannot
be represented losslessly is explicitly unsupported. Do not choose its first
recipient, overwrite repeated facts, or silently discard the rest. A later
representation change requires its own contract decision.

| Result | Meaning |
| --- | --- |
| Observation | Applicable facts, possibly incomplete, with explicit quality and provenance |
| Not applicable | A known unrelated record class; no business facts are produced |
| Unsupported | An expected format, version, multiplicity, or encoding is outside the profile contract |
| Invalid or conflicting | Required interpretation cannot be trusted; independently valid facts may be retained with that qualification |
| Limit exceeded | Processing cannot finish within a configured bound; no clipped success result |

An invalid/conflicting required evidence field cannot appear as a valid confirmed
fact. A consumer must honor the record disposition and field quality, not merely
test whether a value is present. Independently valid context does not repair an
invalid remote-rejection or lifecycle interpretation.

## Field semantics and quality

Field names and meanings are declared by the profile, not copied from arbitrary
source keys. Initial value kinds are strings, integers, booleans, and timestamps.
The contract does not introduce an unconstrained nested event-data bag.

| Field quality | Meaning |
| --- | --- |
| Present | A value was obtained and validated under its declared meaning |
| Missing | The record contains no applicable value; absence may be expected for this record class |
| Invalid | A value is present but cannot be interpreted under the declared contract |
| Conflicting | Eligible producers disagree and the profile has no explicit precedence resolving them |

Reuse an already structured source value only when its semantics are declared.
An envelope sender is not the `From:` header, and an envelope recipient is not the
`To:` header. A source key named `from` is not sufficient evidence of either role.
Source fields cannot overwrite trusted provenance, profile, or quality metadata.

Producer selection is explicit and validated. An invalid primary value does not
silently become valid through a convenient text fallback. If several producers
are eligible, their relationship or precedence must be declared. The block does
not claim to detect contradictions in text it deliberately did not parse.

Missing subject or sender in a recipient-result record can be an ordinary partial
observation: another record may contain the context. It is not an error for every
line to lack every notification field. Correlation/enrichment owns waiting,
history requests, and the final decision that required context is unavailable.

Malformed present fields, conflicts, and unsupported expected formats remain
observable immediately through safe issue codes and bounded diagnostics. This
does not authorize an immediate terminal business failure or an error notification
for every partial observation. Known unrelated records are counted normally,
without being logged as processing failures.

## Deterministic processing

For a fixed source record, profile revision, requested fields, and stable semantic
references, extraction produces the same business facts. It does not consult the
current clock, random values, network services, or mutable process-local context.

Acquisition time may differ on replay and remains provenance only. It cannot be
used to infer a missing year, timezone, or business timestamp. Any semantic
reference used by an explicitly supported format must come from stable source
data or be fixed and reused by the processing contract. The extractor does not
create a private durable cache to make such inference appear deterministic.

Proposed processing sequence:

1. Select the explicitly configured profile and applicable declared record class.
   Do not guess by running every available parser until one returns values.
2. Determine needed fields and mandatory interpretation evidence. Reuse shared
   extraction work for multiple rules rather than parsing the same field per rule.
3. Obtain values through declared source-field mappings or bounded text capture,
   then perform explicit type/time/subject conversion.
4. Validate value meanings, required evidence, producer relationships, and limits.
   Return quality/provenance and safe issues without manufacturing defaults.
5. Release record-local scratch data after handoff. Do not retain an unbounded
   cache of source records or normalized observations.

The initial mechanism set is direct field mapping, named regular-expression
captures, and explicit conversions. Use bounded Go regular expressions, not an
arbitrary-code rule language, shell commands, or executable plugins. Compile
validated patterns when accepting configuration, not for each record. Exact
configuration syntax and field-dependency declarations remain
[open](open-decisions.md#configuration-and-state-compatibility).

## Postfix facts, not mail-event decisions

The profile can describe observed receipt/context, queue, recipient-result, and
removal markers. It extracts originating-source coordinates, queue ID, address
roles, applicable timestamps, status markers, and unambiguous SMTP-response
evidence. A removal marker is an observation, not a universal conclusion about
every recipient or a replacement for lifecycle correlation.

`status=bounced` does not become a confirmed remote rejection here. Text that
contains a 5xx code does not automatically become a remote SMTP response. When
attribution or parsing is ambiguous, carry an explicit unsupported/invalid quality
instead of a positive evidence flag. Detection/correlation owns finality, domain
allowlists, queue-ID reuse, and the event decision.

Raw SMTP diagnostics may be transient parser input, but the result carries only
necessary typed evidence, not a generic raw-diagnostic field available to all
destinations. Body, attachments, other recipients, or headers are not collected
as fallback notification content. Source-supplied data remains untrusted even
when it is syntactically valid.

## Subject and time handling

Decode a complete subject value, not a subject guessed from unrelated text or
assembled across records. Supported header folding is unfolded before RFC 2047
decoding, without changing the original record fingerprint. Arbitrary embedded
newlines or extra header material do not become valid folding.

Validate the decoded display value as well as the source representation. Propose
rejecting remaining CR, LF, NUL, and other control characters rather than silently
removing them. A syntactically valid encoded word that decodes to such characters
is not an acceptable display subject. Destination escaping remains a separate
formatting responsibility; this validation does not make the value trusted markup.

Malformed encoded words, invalid UTF-8, unsupported charsets, and known source
truncation have explicit outcomes. Do not silently replace undecodable bytes,
send encoded text as a substitute for required decoded subject, or invent omitted
characters. A forgiving library decoder is not proof that malformed-looking input
is valid: the supported cases and failure behavior require tests. Charset coverage
and any additional decoding dependency remain
[open](open-decisions.md#mail-scenario).

Keep three times distinct: source search time, acquisition/observation time, and
the relevant business time. The agreed mail notification timestamp means receipt
by the outbound relay. It must be supported by the declared source-field meaning
or receipt evidence, not substituted from the message `Date:` header. Missing
required time or timezone is not repaired from the machine's local timezone or
the current time.

## Persistence, failures, and revisions

The extractor owns no progress or retry state. Processing accounts for accepted
record effects together with replay protection and required follow-up work under
the approved ingestion boundary. A record-level unsupported/invalid result is not
a transport failure; it can be durably accounted for without retaining the raw
record or repeatedly failing the same source read.

Whether valid partial facts create durable correlation work belongs to the next
block. A processing failure must not silently become a complete event. Safe error
information can include declared field names, profile ID, and bounded error codes,
not subjects, addresses, raw diagnostics, queue IDs, or fingerprint values in logs
and metric labels.

Profile revision and field provenance accompany observations needed by downstream
work. Changing a parser does not automatically replay accepted history or mutate
already admitted events/jobs. Compatibility and explicit reprocessing are governed
by the [configuration/state contract](open-decisions.md#configuration-and-state-compatibility).

## Proposed limits

The source-record size and field bounds are inherited from the approved ingestion
contract. The following additional defaults are **proposals, not approved or
benchmarked**:

| Setting | Proposed initial value |
| --- | --- |
| Normalized fact fields per observation | 32, with declared names |
| Total normalized fact content | 16 KiB |
| Decoded subject | 8 KiB, also within the total content limit |
| Regular-expression patterns per profile | 32 |
| Single pattern text | 4 KiB |

Exceeding an output limit produces an explicit failure, not a silently truncated
subject or partial success assembled by dropping fields. Bound conversion and
decoding buffers before allocation, including charset expansion. Record-local
scratch/output allocations count against the shared ingestion buffer budget;
there is no independent unbounded extraction queue.

Finite input size, pattern count, and bounded regular-expression behavior limit
work, but do not establish a benchmarked CPU latency or process-RSS guarantee.
Configuration must also bound the overall number of profiles/producers. Observe
processing duration and limit failures with bounded, non-sensitive labels.

## Proposed test criteria

- Declared structured fields and supported text forms produce equivalent facts;
  ignored source keys cannot overwrite metadata or change field meanings.
- Header addresses cannot substitute for envelope addresses. Status text or an
  unrelated 5xx substring cannot manufacture confirmed remote-rejection evidence.
- Expected partial records differ from malformed present fields, conflicting
  producers, known unrelated classes, and unsupported expected formats.
- Multiple independent results in one unsupported representation are not reduced
  to the first recipient or overwritten into one scalar value.
- Fixed profile and stable semantic references produce identical facts on replay,
  even when acquisition time changes. Normalization never changes the fingerprint.
- Missing year/timezone and different search/business times do not introduce
  machine-clock or local-timezone inference.
- Subject cases cover plain text, multiple encoded words, supported folding,
  unsupported charsets, malformed words, invalid UTF-8, known truncation, and
  control/header-injection characters both before and after decoding.
- Pattern, field, record, output, and expansion limits fail explicitly without
  clipping, uncontrolled allocation, or retained per-record caches.
- Configuration rejects unsupported profiles, invalid producer relationships,
  invalid patterns, and unresolved semantic dependencies before processing.
- Diagnostics contain bounded codes and declared names, not source values or
  sensitive identifiers. No error notification is emitted by this block itself.
- Processing integration covers durable accounting of partial/error outcomes and
  replay without duplicate business effects. Those are processing guarantees, not
  guarantees of calling a stateless extractor twice.

Use independently written synthetic fixtures and reserved example domains. No
private deployment configuration, logs, or parser implementation is a source for
public fixtures. These are proposed acceptance criteria, not implemented tests.
