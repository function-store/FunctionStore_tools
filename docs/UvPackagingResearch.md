---
status: research
summary: Research into shipping tools as uv/PyPI packages. Explicitly NOT the plan — the bucket/manifest rail won.
since: 2026-08-10
superseded_by: docs/ConfiguratorDistribution.md
---

# uv-Packaged TD Tools — Research Notes

Research into whether individual FunctionStore tools could ship as
installable, dependency-driven `uv`/PyPI packages instead of (or alongside)
the current `.tox`-drop-in + [RegistryScheme](RegistryScheme.md) model.
Nothing here has been implemented — this is groundwork to act on later.
The pick-and-choose install/configurator design that sits on top of this
delivery layer lives in
[ConfiguratorDistribution.md](ConfiguratorDistribution.md).

## 1. The question

Could each tool (`OpTemplates`, `FNS_Toolbar`, `PreviewPanel25`,
`FNS_Navbar`, `VSCodeTools`, etc.) become an independently-versioned package
with real dependency resolution — `uv add tdp-OpTemplates`, transitive deps
pinned in a lockfile — rather than a manually-downloaded `.tox` release?

**The fork that matters**: `uv`/PyPI can only ever distribute the
*pure-Python layer* of a tool (extensions, helper modules) with genuine
dependency resolution. It cannot materialize an operator network — COMPs,
parameters, wiring, UI — into a running `.toe`. That still requires a
`.tox` to be loaded into the network somehow. So "packaging via uv" is
really a question of **delivery mechanism for the `.tox` artifact and its
companion Python**, not a replacement for RegistryScheme's runtime
dependency system (host registers into a `/sys` global, semver-checked,
self-healing — see [RegistryScheme.md](RegistryScheme.md)). The two are
orthogonal: uv could version/deliver the `.tox`; RegistryScheme still owns
the in-project relationship between a tool and the registry it publishes
into.

## 2. Reference implementation: tdp-MVP

[PlusPlusOneGmbH/tdp-MVP](https://github.com/PlusPlusOneGmbH/tdp-MVP) is a
working minimal example of exactly this pattern. Repo layout:

```
pyproject.toml
uv.lock
src/tdpMVP/
├── __init__.py                    # re-exports sub-tox-modules, builds _ToxFiles dict
└── ExposeableTox/
    ├── ExposeableTox.tox          # the actual TD component, shipped as package data
    ├── __init__.py                # exposes ToxFile (Path), DefaultGlobalOpShortcut, Typing
    ├── extExposeableExtension.py  # the extension source, externalized-style
    └── some_relative_data.py
AppData/Scripts/sys.py             # the sys.path injection hack (see §3)
.packagefolder                     # manifest the hack reads
.touchdesigner-version              # 2023.12480 — pins target TD build
.python-version                     # 3.11.1
```

### 2.1 Packaging conventions

- **Naming**: PyPI package prefixed `tdp-<Name>` (searchable/discoverable on
  the index); top-level import module drops the dash (`tdp-MVP` →
  `tdpMVP`) since Python identifiers can't contain one.
- **`pyproject.toml`** (per component):
  ```toml
  [project]
  name = "tdp-ExposeableTox"
  requires-python = ">=3.11.10"   # match TD's embedded Python
  dependencies = []

  [tool.uv]
  environments = ["sys_platform =='win32'", "sys_platform =='darwin'"]

  [dependency-groups]
  dev = ["monkeybrain>=0.2.3"]     # TD-version-enforcing dev tool, see §2.4

  [tool.monkeybrain]
  touchdesigner-version = "2025.32820"
  enforce-version = "strict"        # strict | closest-build | latest-build | latest-version
  projectfile = "Project.toe"

  [build-system]
  requires = ["setuptools>=61.0"]
  build-backend = "setuptools.build_meta"

  [tool.setuptools.packages.find]
  where = ["src"]

  [tool.setuptools.package-data]
  "*" = ["*.tox"]   # otherwise the binary tox is dropped from the wheel/sdist
  ```
- `uv.lock` gives real transitive dependency resolution per tool — the
  thing RegistryScheme's storage-based semver check doesn't attempt.

> **Clarifying a likely misread**: `package-data` does not mean "Python
> files only." Wheels/sdists can carry arbitrary binary assets — the
> `"*.tox"` glob tells the build backend to bundle the compiled `.tox`
> **binary, byte-for-byte, as-is**. Nothing about the operator network
> gets reconstructed via Python. The pipeline is: build the tool normally
> in TD (Embody-tracked) → `op.Embody.ExportPortableTox(...)` compiles it
> to a real `.tox` (same artifact already shipped via `modules/release/`
> today) → that binary sits next to `__init__.py` and rides along in the
> wheel unchanged → `uv sync`/`pip install` unpacks it into `site-packages`
> verbatim → `mod.pkg.Module.ToxFile` (§2.3) resolves to that installed
> binary's path and **TD loads it with its own native tox-loading code** —
> the same path as opening any `.tox` from disk. `__init__.py` is just a
> locator (`Path(__file__).parent / "X.tox"`) plus type hints, not a
> description of the network's contents.

### 2.2 The component contract

Each tox-backed unit is a small package with a fixed `__init__.py` shape:

```python
from pathlib import Path

ToxFile = Path(Path(__file__).parent, "ExposeableTox.tox")

# Lets several tools share ONE global instance without name collisions.
# A UUID or PACKAGE_COMP-style name both work.
DefaultGlobalOpShortcut = "A897a62dd86534febb0b8-94070756566d"

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .extExposeableExtension import extExposeableExtension
    class Typing(baseCOMP, extExposeableExtension):
        pass
else:
    class Typing:
        pass

__all__ = ["ToxFile", "Typing", "DefaultGlobalOpShortcut"]
```

`DefaultGlobalOpShortcut` is conceptually the same idea as RegistryScheme's
`/sys/<Name>` global-instance promotion — a documented convention for "only
one of these should really exist," just without the runtime
promotion/healing machinery.

A root package re-exports every sub-tox-module and builds a discovery dict:
```python
from . import ExposeableTox
_ToxFiles = {"ExposeableTox": ExposeableTox.ToxFile}   # for a future "TDP-Browser" palette UI
```

### 2.3 The load-time bridge: `mod` → External Tox Path

Once the package is installed into `site-packages`, a COMP's **External
Tox Path** parameter is set to an *expression*, not a literal path:

```
mod.tdpPackageName.ToxModuleOne.ToxFile
```

TD's `mod`-class import (see [MOD_Class](https://docs.derivative.ca/MOD_Class))
resolves the Python module and pulls the tox's absolute path back out — so
the component loads straight from `site-packages`, no drag-and-drop, no
copy into the project.

Because TD's DAT-based `mod` import and a real Python package's relative
import are different mechanisms, component code needs a manual branch to
work under both:
```python
if __package__ is None:
    import some_relative_data      # loaded as a DAT inside TD
else:
    from . import some_relative_data   # loaded as an installed package
```

### 2.4 `monkeybrain`

A companion dev-dependency that pins/enforces which exact TD build a
project requires (`enforce-version = "strict"` etc.) and exposes a `uv run
mb init.files`-style CLI that scaffolds the `.packagefolder` manifest. Not
investigated further — flagged here as the piece that would need
evaluating if this path is pursued.

## 3. The `sys.py` hack (and why it likely isn't needed on current TD)

**The problem it solves**: TD's embedded Python doesn't know about a
project-local `.venv/Lib/site-packages` on its own, and there's no
reliable "run this before anything else" project hook to inject one.

**tdp-MVP's fix**: `AppData/Scripts/sys.py` hijacks the `sys` module
itself. On first import (which happens very early), it reads a
`.packagefolder` manifest —
```
${UV_PROJECT_ENVIRONMENT||.venv}/Lib/site-packages
src
```
(env-var-templated, `||` for a default) — inserts those paths at the front
of `sys.path`, then re-exports every attribute of the real `sys` module so
nothing downstream notices the substitution.

**This targets TD `2023.12480`** (the repo's pinned `.touchdesigner-version`).
Confirmed via the TD wiki: this is no longer necessary on current builds.

## 4. TD's native equivalent: `TDPyEnvManager`

TD ships an official component that does the same job as the hack, with no
custom Python required.

### 4.1 Mechanism

A `TDPyEnvManagerContext.yaml` (legacy: `.json`, auto-converted) placed
**next to the `.toe`** — or, as of a later build, a
`[tool.touchdesigner.TDPyEnvManagerContext]` table directly in
`pyproject.toml` — is read by a `Helper` class baked into **TD's own core
startup sequence**. Per the wiki: the registered environment "will be
added to the Python search path **before any TouchDesigner COMP cooks and
any custom extensions initialized**"
([TDPyEnvManagerHelper](https://docs.derivative.ca/TDPyEnvManagerHelper)).
That is a stronger, earlier guarantee than most project-level hooks give
you — and it's git-committable, unlike the older global "Python 64-bit
Module Path" preference (see §4.4).

### 4.2 Real example (from Derivative themselves)

[TouchDesigner/TDDepthAnything](https://github.com/TouchDesigner/TDDepthAnything)
ships this `TDPyEnvManagerContext.yaml` at its project root:

```yaml
contextVersion: 2
createdByVersion: 1.4.3
active: true
mode: Python vEnv
envName: .venv
installPath: .
pythonVersion: '3.11'
autoSetup: true
autoSetupReqs:
 - requirements.txt
autoSetupSyncReqs: false
extraPaths: []
```

`envName: .venv` + `installPath: .` → `<project>/.venv` — **the exact
default location `uv venv` / `uv sync` already use.** `autoSetup` here
drives TD's own pip-style installer against `requirements.txt`; it isn't
uv-aware, but it's optional — see §5.

### 4.3 Linking an externally-created venv

`tdPyEnvManagerExt` exposes `LinkPyVenv(envPath: pathlib.Path)` — "attempts
to link the current TouchDesigner session to a Python virtual environment,
**given a path to it**." No requirement that TD's own "Create vEnv" button
created it. (`LinkCondaEnv` is the Conda equivalent; needs `LinkConda`
called first.)

**Not confirmed from docs — verify empirically before relying on it**:
whether calling `LinkPyVenv` durably rewrites the context file for the
*next* cold start, or only links the live session. The persisted fields in
the example (`contextVersion`, `createdByVersion`) suggest it's meant to
persist, but no quote confirms it. Hand-authoring the YAML directly (as
Derivative's own example does) sidesteps the question entirely and is the
safer starting point.

### 4.4 Version gating

| Build | Date | What landed |
|---|---|---|
| 2025.30060 | Jun 2025 | Initial `TDPyEnvManager` palette component (venv/conda creation, package mgmt) |
| 2025.31310 | Oct 2025 | `Helper` class loads during **TD core startup**; `TDPyEnvManagerContext.json` auto-read next to `.toe` |
| 2025.32280 | Jan 2025* | Context can live in `pyproject.toml` under `[tool.touchdesigner.TDPyEnvManagerContext]` |
| 2025.33070 | Jul 2026* | Current official build (v1.4.5-era `tdPyEnvManager`); this is what we're targeting going forward |

\* dates as surfaced by search tooling — sequencing (older→newer build
number) is the reliable part, treat exact calendar dates as approximate.

Below 2025.31310 (and definitely on the `2023.x` line tdp-MVP itself
targets, and this project's README-stated floor of `2023.11880`), none of
this exists — the `sys.py` hack or the global, non-portable "Python 64-bit
Module Path" preference (§4.5) are the only options there.

### 4.5 The older, always-available fallback

Edit → Preferences → General → "Add External Python to Search Path" +
"Python 64-bit Module Path" (semicolon-separated paths) + "Search External
Python Path Last". Confirmed via
[Preferences Dialog](https://docs.derivative.ca/Dialogs:Preferences_Dialog).
**This is a global, per-machine setting stored in `pref.txt` outside the
project** — not committable to git, so it can't reproduce the "clone repo,
`uv sync`, open `.toe`, it just works" portability that both the hack and
`TDPyEnvManager` are going for. Only useful as a manual last resort.

## 5. What this means for TD 2025.33070 specifically

On the build we're now targeting, the native mechanism should fully
replace the `sys.py` hack:

1. `uv sync` creates `.venv` at the project root as it does by default —
   no change to normal uv workflow.
2. Hand-author (or use `LinkPyVenv` once and verify it persists) a
   `TDPyEnvManagerContext.yaml` or `pyproject.toml` table:
   ```yaml
   mode: Python vEnv
   envName: .venv
   installPath: .
   pythonVersion: '3.11'      # must match TD 2025.33070's embedded interpreter
   autoSetup: false            # uv owns installs; TD only needs to find the venv
   ```
3. TD's core `Helper` picks this up at startup, before any COMP cooks or
   extension inits — same guarantee the hack manufactured by hand.
4. `.packagefolder` and the fake `AppData/Scripts/sys.py` become dead
   weight and can be dropped.
5. The actual packaging trick — `.tox` as package data, `mod.pkg.Module.ToxFile`
   in External Tox Path — is unaffected by any of this; it only depends on
   `site-packages` being reachable, however that happens.

**Open items to verify empirically before depending on this** (cheap,
~5-minute checks):
- Does `pythonVersion` need to match TD's embedded interpreter exactly
  (patch-level) or just major.minor? tdp-MVP pinned `>=3.11.10`; confirm
  what 2025.33070 embeds.
- Does `LinkPyVenv` persist to the context file, or is it session-only?
- Does a hand-authored context file pointing at a `uv`-created `.venv`
  (never touched by TD's own "Create vEnv") get accepted as "valid" on
  cold start, or does validity checking expect TD-authored metadata inside
  the venv?

## 6. Multiple packages, one repo: uv workspaces

Individual tools don't need separate repos to be independently-versioned
packages — this is what `uv` workspaces are for
([docs](https://docs.astral.sh/uv/concepts/projects/workspaces/)).

- A root `pyproject.toml` declares `[tool.uv.workspace] members = [...]`
  as glob patterns; every matched directory needs its own `pyproject.toml`.
  Layout is flexible — nested/scattered globs are fine, members don't need
  to live flat under one `packages/` folder.
- Each member is **independently versioned and independently publishable**
  to PyPI (`tdp-OpTemplates`, `tdp-FNS_Toolbar`, `tdp-Navbar`, … as
  separate packages, separate release cadence).
- All members share **one `uv.lock`** and, by default, **one `.venv`**.
  This is a good fit here, not a limitation: `TDPyEnvManagerContext.yaml`
  (§4) points TD at exactly one venv, so a workspace naturally gives one
  context file for the whole repo instead of juggling N environments/context
  files per tool.
- Cross-tool dependencies — the README's "some modules expect the presence
  of others" — become real, resolvable dependencies via `tool.uv.sources`
  with `workspace = true`: editable/local during dev, resolving to the
  normal published version once each package ships independently. This
  replaces an informal comment with an enforced, resolvable graph.

**The wrinkle**: Embody's externalized live-source tree (diffable
`.py`/`.json`/`.tdn`, the whole point of Embody) and tdp-MVP's packaging
convention (`src/pkgname/Module/__init__.py` + `Module.tox` as opaque
package data) are two different representations of the same tool. A
workspace member's directory would realistically hold the **release
artifact** — Embody's `ExportPortableTox` output plus a thin `__init__.py`
— not the live dev tree itself. Mechanically small: point each tool's
`pre_release` hook (already established in
[RegistryScheme.md §6](RegistryScheme.md)) at its workspace-member folder
instead of the flat `modules/release/` folder.

## 7. Relationship to RegistryScheme — not a replacement

Nothing here changes [RegistryScheme.md](RegistryScheme.md). That system
solves a different problem: multiple tools publishing into one shared,
self-healing, semver-checked central manager inside a live project
(toolbar widgets, navbar items, pane types). `uv` + `TDPyEnvManager` would
only ever solve **artifact delivery and Python dependency resolution** —
getting the right `.tox` and its pinned dependencies onto disk and onto
`sys.path`. A tool could plausibly be *both*: uv-delivered as a package,
and a RegistryScheme host once it's in the project. The two systems don't
compete for the same responsibility.

## 8. Next steps (not started)

- [ ] Pick one small standalone tool (no registry-hosting) as a pilot.
- [ ] Verify the three open items in §5 against a real TD 2025.33070
      install.
- [ ] Decide package granularity: one PyPI package per tool (tdp-MVP's
      model) vs. one package with multiple tox-modules (also supported by
      tdp-MVP's root `_ToxFiles` pattern) vs. a uv workspace (§6) spanning
      all tools in this repo.
- [ ] If going the workspace route: decide where release artifacts land
      per member and adjust `pre_release`/`ExportPortableTox` targets
      accordingly.
- [ ] Evaluate `monkeybrain` (§2.4) or decide to skip it.
- [ ] Decide whether `autoSetup`/`requirements.txt` (TD's own installer) or
      pure `uv sync` (manual, outside TD) owns dependency installation —
      they're not mutually required.
