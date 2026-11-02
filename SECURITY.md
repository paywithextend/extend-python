# Security

Report vulnerabilities privately through the repository's GitHub Security
advisory reporting feature when enabled. Otherwise contact the Extend support
channel at support@paywithextend.com and request a private security
handoff. Do not put credentials, customer data or exploit details in public issues.

Version 3 requires an explicit stage/prod environment. API credentials are bound
to that origin, not arbitrary URLs. Redirects are not followed. Applications own
their credential storage and must close clients.

The release workflow requires the PyPI Trusted Publisher for this repository,
release.yml, and the protected pypi environment to be configured before publishing.
Adding workflow YAML does not register that publisher. Do not restore token-based
publishing to bypass a failed configuration check.
