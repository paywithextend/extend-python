# Publishing a release

Releases promote reviewed changes to `main`. Publishing is a separate, manual
operation; merging a release PR does not upload a package.

## One-time publisher configuration

1. Create the GitHub environment `pypi` and restrict deployment branches to `main`.
   Configure the repository's required release reviewers before publishing.
2. On PyPI, configure a Trusted Publisher for the existing `paywithextend` project:
   owner `paywithextend`, repository `extend-python`, workflow `release.yml`,
   environment `pypi`.
3. Verify both configurations before dispatching. The workflow uses GitHub OIDC;
   the legacy `PYPI_API_TOKEN` secret is not used. Do not remove legacy credentials
   until the replacement publisher has been verified.

## Release procedure

1. Update `extend/__version__.py`, the changelog and migration notes together.
2. Open a release PR to `main`; require review and successful Python 3.11–3.14 CI.
3. Merge the release PR. Create the matching `vX.Y.Z` tag at the reviewed main
   commit and push it. Never move a published tag or reuse a published version.
4. Run **Publish reviewed SDK** (`release.yml`) on `main` with that tag.
   The workflow checks tag ancestry and version, lints and tests source, builds
   distributions, tests the installed wheel and checks runtime advisories before
   requesting publication through the `pypi` environment.
5. Confirm the workflow succeeded, both distributions exist on PyPI and a fresh
   installation reports the expected version. Create the matching GitHub release
   from the changelog and link the migration guide.
6. Merge release-only metadata changes back into `development` when necessary.

Publish SDK 3.0.0 before releasing packages that require `paywithextend==3.0.0`.
A successful offline test run does not establish live endpoint availability or
account permissions. See the availability notes in the README.
