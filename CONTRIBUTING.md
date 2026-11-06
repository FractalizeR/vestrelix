# Contributing

Use English and Conventional Commits. Submit changes through pull requests to
`master`. Contributions are under the combined terms in `LICENSE`.

## Publication checks

Python 3.11 or newer and Git are required. Install the pinned Gitleaks binary:

```sh
python3 tools/publication/install_gitleaks.py
```

Install repository-local hooks. If you have an organization-specific publication
policy, supply its absolute path outside the repository:

```sh
python3 tools/publication/check.py install --private-policy /absolute/path/to/policy.json
```

Other contributors must explicitly choose public-only checks:

```sh
python3 tools/publication/check.py install --public-only
```

A private policy is a JSON object with a nonempty `forbidden_terms` array of
strings. Keep it outside Git, restrict its permissions to its owner, and never
copy its values into issues, commits, CI, or examples. Hooks fail when their
configured policy or pinned scanner is unavailable. Hooks are not installed by
Git on clone and can be bypassed; they are safeguards, not a confidentiality guarantee.

Before publication:

```sh
python3 tools/publication/check.py staged
python3 tools/publication/check.py history
python3 -m unittest discover -s tools/publication/tests -v
```

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

Security tools and Actions are version-pinned. Gitleaks downloads are checked
against committed SHA-256 digests. Dependency updates arrive through Dependabot.

The current bootstrap has no Go source. CI enables Go tests, vet, vulnerability
checks, and CodeQL when tracked Go files appear. The module targets Go 1.27.
Do not add placeholder application code solely to make a scanner run.

After changing publication tooling, run its tests and both publication checks.
After changing workflows or Dependabot settings, run actionlint on workflows and
the pinned zizmor check from the repository root, matching CI's collection scope:

```sh
zizmor --offline --no-progress .
```
