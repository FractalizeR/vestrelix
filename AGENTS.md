# Vestrelix agent instructions

- Treat this repository, its history, issues, CI output, and artifacts as public. Do not introduce confidential employer/customer information, real operational data, internal endpoints, or credentials.
- Use synthetic fixtures and reserved example domains. Do not copy implementation, configuration, logs, or requirements containing private details from other projects.
- Use English for code, documentation, comments, and Conventional Commit messages.
- Read `CONTRIBUTING.md` before changing files and `SECURITY.md` before handling a suspected disclosure.
- The primary branch is `master`. After the initial bootstrap, make changes through pull requests; do not push directly to `master`.
- Install publication hooks before committing. Run the staged and history checks described in `CONTRIBUTING.md` before publication; do not bypass missing tools, private-policy failures, or findings.
- Do not add broad scanner exclusions or commit secret-shaped fixtures. Generate sensitive test cases in temporary repositories at runtime.
- Keep private publication policies outside this repository. Public CI cannot check their contents.
- The only permitted tracked symbolic link is `CLAUDE.md -> AGENTS.md`.
- Keep the Apache-2.0 plus Commons Clause licensing combination intact. Do not describe the project as OSI-approved open source or label its license as plain Apache-2.0.
- The application is not implemented yet. Security checks for Go code must become active when Go source files are introduced; do not replace them with unconditional success.
- Development commands and tool setup are in `CONTRIBUTING.md`; run `make check` before publication and the relevant race/security checks for changed Go behavior.
- Add regression tests for bug fixes and derive expected outcomes from `FEATURES.md`. Cover persistence/recovery, duplicate handling, and privacy boundaries when changing those behaviors.
- Do not weaken checks, suppress findings broadly, or change expected test results solely to make CI pass; report blockers instead.
