# Governance

## Decision-making

Hermes Agent is maintained by [Nous Research](https://nousresearch.com). Maintainers
hold final say on merges, releases and scope. Contributions are welcome and arrive
through pull requests; see [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## The rubric decides

`AGENTS.md` carries the contribution rubric — what gets merged and what gets rejected —
and it is the project's intent layer, not a style guide. Two rules follow from it:

- The product surface (platforms, providers, desktop and TUI features) expands
  aggressively and on purpose.
- The **core agent and the model tool schema** are conservative, because every core tool
  is sent on every API call for every user.

A change that grows the waist needs an argued case. A change that grows the edges needs
only to be correct.

## Automated triage

An automated sweeper may close pull requests on exactly three grounds:
`implemented_on_main`, `cannot_reproduce`, and `incoherent`. Taste-based
"we don't want this" or "out of scope" closures are **not** an automated decision — those
stay with a human maintainer. When in doubt, the sweeper leaves the PR open.

## Roles

| Role | Can |
|------|-----|
| Contributor | Open issues and pull requests |
| Reviewer | Review and approve changes in their area |
| Maintainer | Merge, cut releases, set scope, resolve disputes |

Contributors are recorded in `.mailmap` and `contributors/`; `scripts/add_contributor.py`
and `scripts/contributor_audit.py` maintain that record.

## Changing the rules

Amendments to this document, to `AGENTS.md`, or to the release process are proposed as a
pull request and require maintainer approval. Security matters follow
[SECURITY.md](SECURITY.md) and are handled privately until a fix ships.

## Code of conduct

Discussion happens in the issue tracker and on
[Discord](https://discord.gg/NousResearch). Behaviour that makes the project unpleasant
to contribute to is grounds for removal from those channels at maintainer discretion.
