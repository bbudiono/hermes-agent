# Releasing

Hermes Agent versions live in `pyproject.toml` (`[project] version`) and follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- **Patch** — bug fixes, no behaviour change for a working setup.
- **Minor** — new platforms, providers, tools, skills, or CLI commands.
- **Major** — a change that breaks existing configs, stored state, or the plugin/skill
  contract.

## Checklist

1. **Green baseline.** `scripts/run_tests.sh` passes (never bare `pytest` — see
   [TESTING.md](TESTING.md)), the per-workspace JS suites pass
   (`npm test --workspace ui-tui`, `--workspace apps/desktop`, `--workspace web`), and
   CI's `all-checks-pass` gate is green on `main`.
2. **Bump the version** in `pyproject.toml`. Nothing else hardcodes it.
3. **Update [CHANGELOG.md](CHANGELOG.md)** — move `Unreleased` items under the new
   version heading with the release date. A release without an entry is not releasable.
4. **Refresh the docs that track behaviour**: `README.md`, `docs/ARCHITECTURE.md`,
   `docs/ARCHITECTURE_MAP.md`, `docs/INDEX.md`, `docs/DEPLOYMENT_PROCESS.md`,
   `TESTING.md`, and re-export `docs/diagrams/architecture.html` if the source diagram
   changed. If `AGENTS.md` changed, re-copy it over `CLAUDE.md` (keeping the
   do-not-hand-edit header line) — no generator or CI check does this for you.
5. **Verify the install paths** still work end to end: `scripts/install.sh`
   (Linux/macOS/WSL2), `scripts/install.ps1` (native Windows), the Docker image, and the
   Nix flake.
6. **Tag and release.** `git tag vX.Y.Z && git push origin vX.Y.Z`, then publish the
   GitHub release with the changelog section as its body.
7. **Publish artifacts** — wheel and container image via the packaging workflows.
8. **Verify after the fact**: a clean install of the published version starts, `hermes
   model` lists providers, and the gateway reaches ready state.

## Hotfixes

Branch from the release tag, apply the minimal fix, bump the patch version, add a
changelog entry, release, then merge back to `main`. Hotfixes skip nothing in the
checklist above except step 4 where no documented behaviour changed.

## Rollback

Releases are additive: reinstall the previous version from PyPI or pull the previous
container tag. Stored session state is forward-compatible within a major version, so a
downgrade inside the same major line is safe. Downgrading across a major version requires
the migration note published with that major release.
