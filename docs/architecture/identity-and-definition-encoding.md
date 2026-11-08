# Identity and definition encoding

**Status: selected technical specification under delegated architectural design.
Not implemented or encoder/compiler/source-conformance-verified.**

This specifies canonical envelopes, not Go interfaces, SQL tables, a configuration
schema, or permission to implement the application. Owners still define identity
meaning. In particular, an encoding cannot supply missing Postfix lifecycle proof.
Concrete definition AST bodies belong to the complete configuration specification.

## C1 canonical value model

Use RFC 8949 section 4.2.1 **Core Deterministic Encoding**, named `c1` here:

- Definite lengths, preferred integer/length representations, and map keys sorted
  by their encoded-byte lexicographic order. Do not select a library's differently
  named "canonical" mode without verifying the exact ordering.
- Values are null, booleans, signed 64-bit integers, byte strings, valid UTF-8 text,
  ordered arrays, or maps with unique text keys. No tags, undefined values,
  native floats, indefinite items, duplicate keys, or invalid UTF-8. Other CBOR
  simple values are forbidden; `false`, `true`, and `null` are the exceptions.
- Text is preserved without trimming, case folding, Unicode normalization, or
  replacement. Domain-specific normalization happens before encoding only where
  its owner explicitly defines it. Byte strings are not interchangeable with text.
- Missing is absence of an optional map member, not null, empty text, zero, or an
  empty array. A required field cannot be omitted. Explicit null is valid only
  where its owning model permits it. Array order is meaningful; a set-like field
  must specify its ordering rather than rely on map/arrival order.
- Time is the tagged array `['time', seconds, nanos]`: signed Unix seconds and
  integer nanoseconds from zero through 999,999,999, in UTC. Duration is
  `['duration-ns', nanoseconds]`, a nonnegative signed-64-bit count. Owner bounds
  still apply. Neither representation permits invented timezone or acquisition time.
- A JSON numeric literal in a semantic definition is
  `['json-number', coefficient, exponent]`, where coefficient is an ASCII decimal
  string with an optional minus sign and no leading zeros, and exponent is a
  signed-64-bit integer. Remove coefficient trailing zeros while increasing the
  exponent; zero is exactly `['json-number', '0', 0]`. Reject overflow/oversize
  input before expensive conversion. This preserves decimal meaning without an
  intermediate binary float; ordinary typed settings remain integers.

The displayed arrays are notation, not YAML or executable code. Semantic models
declare their allowed members and types; generic CBOR validity is insufficient.
Decode into a bounded reviewed model, reject trailing items and unknown fields,
and require re-encoding to yield identical `c1` bytes before accepting stored
canonical content. Parsing/allocation, output bytes, and sorting scratch space
count against owning block budgets. CBOR does not create additional capacity.

Use a maintained encoder, not a local generic CBOR implementation. The initial
candidate is `github.com/fxamacker/cbor/v2` with core-deterministic options and a
closed bounded decoder configuration. Version/license/dependency review, numeric
model handling, native resource checks, and cross-implementation vectors remain
gates; no dependency is installed or pinned by this document.

### Envelope notation and field types

All quoted literals below are CBOR text strings. Envelope/shape versions written
as `1` are integer values, not text. Variable identifiers (`logical_source_id`,
`input_id`, `stable_view_id`, `row_profile_id`, `relay_namespace`, `rule_id`,
`destination_id`, `logical_id`, `kind`, `semantic_format`, `interpreter_contract`,
`binding_revision`, `profile_type`, and `semantics_version`) are bounded ASCII text
identifiers under their owning model, with no implicit case conversion. Queue IDs,
canonical local parts, and domains are ASCII text, not integers or byte strings.

Named `*_bytes` identity/digest fields are CBOR byte strings: SHA-256/HMAC values
are 32 bytes and case/installation IDs are 16 bytes. `revision_bytes` is a
32-byte definition digest. `view`, `generation`, `recipient`, `origin`,
`profile_contract`, dependencies, and time/duration/number shapes are arrays in
the exact displayed order. `row`, definition `body`, and `actual_values` are
maps; their declared value types do not follow a decoder's inferred defaults.
The `headers` map values and `url` member below are byte strings, while source
row field names and values are UTF-8 text. These exceptions are intentional.

## Record fingerprint

For the initial VictoriaLogs raw-row profile, the authorized JSONL row is a map of
UTF-8 field names to strings, including the source's stable returned metadata.
Reject duplicate JSON names or non-string values under this profile instead of
coercing them. The supported API/version must establish that this is the complete
authorized row representation. No configured projection or computed-query fields
are permitted. Acquisition time/request/batch metadata is outside that row.

The canonical envelope is:

`['vestrelix', 'record', 1, view, row]`

`view` is `[logical_source_id, input_id, stable_view_id, row_profile_id]`.
`row` is the complete source string map. Its strings, including the API's source
timestamp spelling, remain exact; only outer JSON encoding/key order disappears.
Source/API representation changes require compatibility review, not automatic
reinterpretation. The fingerprint is SHA-256 of the envelope's `c1` bytes.

View IDs are stable admitted identities, not automatically generated from query
digests, credentials, labels, or HMAC evidence. Input/view equivalence follows the
ingestion contract; no global cross-input replay identity is invented. Retain
fingerprints/protection metadata, not canonical copies of every raw source row.

## Mail occurrence and delivery identities

After lifecycle proof, encode a mail generation as:

`['postfix-generation', 1, relay_namespace, queue_id, receipt_anchor]`

The relay namespace identifies the originating Postfix queue instance, not merely
a convenient host label. Queue ID bytes/case are preserved. `receipt_anchor` is
the validated authoritative start time in the C1 time representation. Duplicate
representations of one start must converge on the same proven anchor. Missing,
competing, or indistinguishable starts remain unresolved; do not add observation
time, a random suffix, or a triggering record fingerprint to make them unique.

For the first rule, the occurrence envelope is:

`['vestrelix', 'mail-occurrence', 1, rule_id, generation, recipient, 'permanent-remote-rejection']`

`recipient` is `['smtp-mailbox', local_part, domain]`. The local part is the
lossless ASCII value after supported SMTP quoting/quoted-pair parsing, preserving
case and plus tags; the matched ASCII DNS domain is lowercase. Source syntax and
punycode/address validation still require the profile's parser evidence. This key
does not contain a sender fallback or Unicode conversion. A null reverse path is
the separate sender fact `['null-reverse-path']`, never a missing recipient.

The stable event ID is SHA-256 of the occurrence envelope's `c1` bytes. Retained
minimal occurrence data checks compatible identity reuse; definition digests,
templates, detection time, budgets, and network attempts do not enter this key.

The delivery envelope is:

`['vestrelix', 'delivery', 1, origin, destination_id]`

For business events, `origin` is `['business', event_id_bytes]`. For notices it is
`['processing-error', case_id_bytes]` or `['system', case_id_bytes]`, using the
owning durable case's stable opaque identity. Case IDs are 16 cryptographically
random bytes created once with the case and reused across its updates/restart,
not generated per retry or quota window. The delivery ID is SHA-256 of this
envelope's `c1` bytes. A manual round never changes it.

Digest bytes are exactly 32 bytes, not an ambiguously decoded text value. A local
tool may display lowercase hexadecimal, but hashes and encoded identities remain
private metadata, not automatic log fields, public examples, or metric labels.

## Semantic definition revisions

The definition envelope is:

`['vestrelix', 'semantic-definition', 1, kind, logical_id, semantic_format, interpreter_contract, body, dependencies]`

`kind`, `semantic_format`, and `interpreter_contract` are explicit supported
identifiers. `body` is the validated minimal typed semantic AST, with effective
defaults materialized and display labels/comments excluded. It is not original
YAML, a client/environment dump, or an executable closure. The future concrete
configuration model must declare every body's fields; this envelope is not a
permissive substitute for that specification.

`dependencies` is an array of `[kind, logical_id, revision_bytes]` triples, unique
by kind/logical identity and sorted lexicographically by their `c1` encodings.
The revision is SHA-256 of the whole envelope's `c1` bytes. Dependencies and bodies
must be persisted with/before referencing admission, under existing count/byte
limits. Interpreter compatibility is explicit: a digest match alone does not
prove equal meaning, and a newer binary cannot silently reinterpret an old body.

Retained definitions contain binding logical identities/revisions, not resolved
URLs/authentication bytes. External reference paths/names are resolver selection,
not evidence of business identity. Query literals and field policies can still
be private even when nonsecret. A definition-format change must preserve old
interpreters or visibly pause dependent work.

## Binding evidence and installation key verifier

Use the separately initialized 256-bit installation identity key with
HMAC-SHA-256 over `c1` bytes of:

`['vestrelix', 'binding', 1, role, logical_id, binding_revision, profile_contract, actual_values]`

`role` is exactly `source` or `target`. `profile_contract` is
`[profile_type, semantics_version]`, using supported bounded identifiers, not a
binary build hash. For both initial roles, `actual_values` is exactly the map
with required `url` and `headers` members. `url` is the byte string of the
immutable connection URL representation used by the client. `headers` is a map
of all configured static connection/authentication header names to exact value
byte strings, empty when none are configured. HTTP header names are ASCII
lowercase with duplicates rejected. Generated content-length/body metadata is
not an authentication header. Dynamic signing/authentication is not part of these
initial profiles.

For VictoriaLogs, explicitly materialize AccountID and ProjectID headers, including
zero defaults, into both the immutable request settings and this header map.
Work-varying source query/time bounds belong to the pinned acquisition semantics,
not a new connection revision per request. Opaque URL contents and header values
are not decoded, trimmed, or guessed equivalent.
Source query/identity semantics remain pinned separately; the tag is not a source
view namespace or proof of complete selection.

Include every generic webhook authentication/header value that might select an
audience. No generic authentication-only rotation exception exists. A verified
profile exception requires its own versioned contract. HMAC creation and I/O use
the same immutable resolver object; configuration input and a later re-read file
cannot be compared as one object but sent as another.

The independent key verifier is HMAC-SHA-256 over:

`['vestrelix', 'identity-key-verifier', 1, installation_id_bytes]`

The installation ID is 16 cryptographically random bytes initialized once. Store
verifier/tag bytes and version in private control metadata/state as appropriate,
never the identity key or resolved secrets in SQLite. Compare tags in constant
time. Missing/wrong key, unsupported evidence, or unverifiable actual values fail
closed. Secret rotation does not regenerate the installation key.

## Compatibility and evidence gates

Envelope/domain versions distinguish formats, not permission to reset protection.
An incompatible encoding, view, anchor, or interpreter change blocks affected
activation until a supported explicit transition exists. Never generate another
input/rule/destination identity to bypass retained obligations or replay markers.

Require independently written vectors for every envelope, map order/UTF-8 cases,
missing/null distinctions, decimal/time boundaries, malformed/oversize CBOR,
definition closure changes, source representation duplicates, and HMAC resolver
continuity. Vectors must distinguish record, occurrence, notice, delivery,
definition, source binding, target binding, and verifier domains. Cross-language
equality is an acceptance condition, not established by choosing CBOR.

## Public references

- [RFC 8949 core deterministic encoding](https://www.rfc-editor.org/rfc/rfc8949.html#section-4.2.1)
- [RFC 2104 HMAC](https://www.rfc-editor.org/rfc/rfc2104.html)
- [Candidate CBOR encoder](https://github.com/fxamacker/cbor)

These references do not replace native, compiler, driver, or deployment evidence.
