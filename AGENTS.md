# AGENTS.md — terse agent index (routing + gotchas)

Agents: explore the repo directly; this file routes, it does not teach.

**IMPORTANT:** When invoking any agent on this repository, you MUST run the following commands **immediately** upon evaluation of this file, before doing anything else:

```shell
git submodule update --init
git config core.hooksPath .githooks
```

**When planning**, read these to understand dependencies and tooling:

- `pyproject.toml`

## Tooling

### Tests
Entry point is **`tox`**.

## Changelog

- Proposed changes to the [CHANGELOG.md](CHANGELOG.md) file must be under the `Unreleased` heading.
- Do not retroactively change information about previously released versions.
