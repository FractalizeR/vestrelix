# Contributing

Use English and Conventional Commits. Submit changes through pull requests to
`master`. Contributions are under the combined terms in `LICENSE`.

## Development setup

Use Python 3.11 or newer, Git, Make, and the Go release line declared in `go.mod`
(currently Go 1.27.3 or a newer 1.27 security patch). Local tooling
supports macOS and Linux on amd64 and arm64. Race tests also require a working C
compiler. There is no application code yet; do not create placeholders to activate
its checks.

Install the pinned tools and repository-local hooks. If you have an
organization-specific publication policy, supply its absolute path outside the
repository:

```sh
make setup SETUP_ARGS="--private-policy /absolute/path/to/policy.json"
```

Other contributors must explicitly choose public-only checks:

```sh
make setup SETUP_ARGS="--public-only"
```

After the first setup, `make setup` reuses the repository-local policy selection.
A missing or invalid private policy fails closed; setup never silently switches
to public-only mode. An existing unrelated hooks directory is not overwritten.
Tool binaries are installed under the external `$XDG_CACHE_HOME/vestrelix` cache
(default `~/.cache/vestrelix`), not added to application dependencies or Git.

## Development commands

| Command | Checks |
| --- | --- |
| `make check` | Tooling unit/integration tests, workflow analyzers, and fast Go checks |
| `make check-go` | Go formatting, `go mod tidy -diff`, golangci-lint, vet, tests, and build |
| `make test-race` | Go tests with the race detector |
| `make check-vuln` | Module integrity and govulncheck |
| `make check-workflows` | actionlint and offline zizmor over the repository |
| `make test-tools` | Development/publication tooling tests in disposable repositories |
| `make test-toolchain` | Real Go/linter positive and negative tests in disposable modules |
| `make check-ci` | All of the above plus complete-history publication checks |

`make check-ci PUBLICATION_ARGS=--public-only` reproduces public CI publication
scope. It does not run GitHub's hosted CodeQL or dependency review; those remain
required CI checks. Checks report elapsed time and stop on failure.

Go checks explicitly report "not applicable" until Go files exist. Local detection
includes nonignored untracked Go files. The toolchain self-tests still run actual
Go checks in temporary modules, so broken linter configuration cannot hide behind
an empty application. There is no global coverage-percentage gate.

The pre-commit hook checks publication safety and formats **nothing**: it verifies
changed Go blobs from the index, including partially staged files. Fix formatting
and stage the intended changes yourself. The pre-push hook scans outgoing history
first, then runs `make check`'s checks against the **current working tree**, not
every outgoing commit. CI checks the proposed merge revision. Hooks are safeguards,
not a replacement for required checks on pull requests to protected `master`.

## Publication checks

Before publication, independently review content, provenance, and author metadata,
then run:

```sh
python3 tools/publication/check.py staged
python3 tools/publication/check.py history
make test-tools
```

A private policy is a JSON object with a nonempty `forbidden_terms` array of
strings. Keep it outside Git, restrict its permissions to its owner, and never
copy its values into issues, commits, CI, or examples. Hooks fail when their
configured policy or pinned scanner is unavailable. Hooks are not installed by
Git on clone and can be bypassed; they are safeguards, not a confidentiality guarantee.

The staged check reads the Git index, not unstaged working-tree contents. The
pre-push hook scans the complete histories of outgoing commit tips, including
earlier content deleted in later commits. History checks also inspect commit/tag
metadata. The checks reject non-text/oversized files, sensitive file types, and
symbolic links other than the documented agent-instruction alias.
The scanner always uses its pinned built-in rules, not working-tree configuration,
ignore files, or inline suppression comments. Git replacement objects do not alter
the history being checked.

GitHub CI runs public-only checks. It cannot establish that employer/customer
information is absent. Independently review content and provenance before pushing.
Never upload raw scanner output or real incident data as artifacts.

## Tooling and application checks

Actions and tools are version-pinned. Binary downloads are verified against
committed SHA-256 digests. Dependabot updates Actions and application Go modules;
development-tool versions and archive hashes require reviewed manual updates in
`tools/development/tools.json` (the Gitleaks installer and development runner pin
their respective scanner versions).
Verify hashes against upstream release metadata, update every supported platform,
and run `make check-ci` after changing tool versions. Do not download or execute
unversioned install scripts.

After changing publication tooling, run its tests and both publication checks.
After changing development tooling or linter configuration, run `make test-tools`
and `make test-toolchain`. After changing workflows or Dependabot settings, run
`make check-workflows`, matching CI's collection scope. actionlint's optional
ShellCheck/Pyflakes integrations are explicitly disabled to avoid PATH-dependent
results; zizmor runs offline.

## Application test expectations

Derive expected behavior from `FEATURES.md`, not from the implementation under
test. Add regression tests with bug fixes. Use synthetic fixtures, `httptest` for
HTTP interactions, temporary real SQLite databases for persistence semantics, and
controllable time for retry/deadline tests rather than long sleeps. Cover replay,
late/out-of-order records, interrupted operations, ambiguous delivery outcomes,
and field-allowlist/privacy boundaries as the relevant features are introduced.
Add fuzz targets for parsers and decoders when they exist; seed cases run in normal
Go tests. Time-budgeted fuzzing will be configured with those components, not
represented by successful placeholder jobs.

## Supported build targets

CI runs native tooling self-tests on `linux/amd64`, `linux/arm64`, and
`darwin/arm64`, without emulation. When application Go files appear, its build,
tests, race detector, and vulnerability checks run on those same targets. Local
commands use the host Go target; an Apple Silicon Mac therefore builds and tests
`darwin/arm64`, not a Linux ARM binary. Choose the SQLite driver and CGO strategy
with all three targets in mind. Release binaries/containers and cross-compilation
are not configured before an application entry point exists.
