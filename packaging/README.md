# Packaging

Machinery for shipping the toolkit as **pickable packages** instead of one
monolith — step 2 of `docs/ConfiguratorDistribution.md` §4. The dependency
audit that gates all of this is §1.1 of that document.

```
catalog.json        curated: category + description (the only hand-written data)
build_manifest.py   runs inside TD; derives everything else, writes manifest.json
manifest.json       generated catalog the configurator and UPDATER both read
configurator/       static picker over manifest.json -> selection.json
dist/               exported .tox artifacts (gitignored; rebuild on demand)
```

## Regenerating the manifest

From a session with TD running:

```python
exec(open('packaging/build_manifest.py').read()); result = Build()
```

Add artifacts (slower — each package is staged and exported through its own
`pre_release` hook):

```python
result = Build(export=True)                     # everything
result = Build(export=['AutoRes', 'ColorUI'])   # named subset
```

Artifact hashes for packages you did not re-export are carried over from the
previous `manifest.json`, so partial rebuilds do not lose data.

## What is derived vs curated

**Derived live** — package list, version/build, surfaces, dependencies,
optional integrations, op counts, help URLs, artifact hashes. Re-running the
generator picks up reality.

**Curated in `catalog.json`** — `category` and `description` only: the two
things the project genuinely cannot tell us. Descriptions were seeded by
inspection and **need owner review**.

## The dependency model

Tools depend only on **core**, never on each other, so the configurator needs
no solver. That is enforceable rather than merely asserted: registry masters
live in core and tools ship stamped *hosts*, so a package's `requires` is
exactly the core packages owning the registries it hosts. Every tool requires
`FNS_Config` (settings persistence); a tool with a toolbar button also
requires `FNS_Toolbar`, and so on.

Anything a package reaches for beyond that is an **optional integration**
(`integrates_with`) and must degrade when the other package is absent — the
guarded-lookup idiom from `ConfiguratorDistribution.md` §1.1. The generator
detects both reference forms, bare `op.X` *and* guarded
`getattr(op, 'X', None)`; missing the guarded form would under-report exactly
the correctly-written integrations.

## Package identity

A shippable package is a depth-1 COMP that is a tracked `pi_suspect` with its
own `.tox`. That is already the project's unit of distribution, so no second
list has to be maintained by hand — add a tool the normal way and it appears.
