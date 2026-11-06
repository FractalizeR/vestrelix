# Vestrelix

Stateful event notifications from logs, built with Go and SQLite.

Vestrelix is being designed as a small, single-process service that reads records,
detects and enriches events, persists delivery jobs, and sends notifications to
independent destinations. The application is not implemented yet.

Planned capabilities include a VictoriaLogs input, configurable event rules,
HTTP notifications, persistent retries, and Prometheus-compatible metrics.

See [Functional scope](FEATURES.md) for the agreed requirements, initial acceptance
scenario, extension points, and open design decisions.

## Development

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Publication checks and repository
security tooling are available; there is no runnable application or release yet.

## Security

Do not submit credentials, real logs, private infrastructure details, or personal
data. See [SECURITY.md](SECURITY.md) for private vulnerability reporting.

## License

Copyright 2026 FractalizeR and contributors.

Vestrelix is **source-available**, under Apache License 2.0 **subject to the
Commons Clause License Condition v1.0**. It is not OSI-approved open-source software.
The complete combined terms are in [LICENSE](LICENSE).

Commercial use within another product is not generally prohibited. The Commons
Clause restricts selling products or services whose value derives entirely or
substantially from this software's functionality, including certain hosting and
support offerings. This summary does not replace the license text. Outputs are
not automatically placed under this license merely because Vestrelix produced them.
