# Security policy

There are no supported application releases yet.

## Reporting a vulnerability

Use GitHub private vulnerability reporting:
<https://github.com/FractalizeR/vestrelix/security/advisories/new>.

Do not open a public issue containing credentials, personal data, real logs,
private addresses, or exploitation details that would expose affected systems.
Use synthetic reproductions and redact sensitive information before submission.
If private reporting is unavailable, do not publish sensitive details; request a
private reporting channel from the maintainer without including the details.

## Publication safeguards

Local staged/pre-push checks use Gitleaks and publication-policy checks. GitHub
adds secret scanning and push protection where supported. These mechanisms do
not detect every secret or every form of confidential information. CI happens
after publication and is not a substitute for checks before pushing.

If a credential is exposed, revoke or rotate it first. Removing a file or
rewriting Git history alone does not make the credential safe again. Coordinate
history cleanup with the maintainer; do not repeat exposed values in reports.
