# TouchDesigner's Text-Based Project Format — What It Actually Is

Research note, 2026-08-21. Read-only investigation: no code changed. Companion
to [TextFormatInjectionStrategy.md](TextFormatInjectionStrategy.md), which
covers what this means for FNSTools distribution.

## 1. This is real, and we have a live sample

Derivative is building an alternative, **text-based** save format for `.toe`
project files (and, presumably, `.tox` components) to sit alongside the
historical opaque binary format. It is **not** the same thing as
`toeexpand`/`toecollapse` (Derivative's existing binary-to-ASCII round-trip
utility for support/diagnostics) — this is a native save mode, controlled by
project settings baked into the file itself.

`C:\VJ\TD\Projects\Test26\Test26.toe` (469 KB) is a real project already saved
in this mode. `file` reports it as plain JSON text. Its header:

```json
"header": {
  "build": "2026.20655.2",
  "settings": {
    "td.settings.project.file-format": "text",
    "td.settings.project.file-structure": "single",
    "td.settings.project.save-runtime-state": true,
    "td.settings.project.save-userdata": "internal"
  }
}
```

Confirmed against Derivative's own channels:

- The [Experimental:File Types](https://derivative.ca/UserGuide/Experimental:File_Types)
  wiki page does not document it yet — it is genuinely undocumented.
- A [forum thread](https://forum.derivative.ca/t/toe-files-in-text-format/309048)
  (staff-confirmed, last public status ~October 2025) says the format is
  "still a very active project," was **deprioritized for the 2025 release**
  in favor of the new POPs operator family, and is expected as **a major
  feature of the release after 2025** — i.e. lines up with a TD 2026 push,
  which matches our sample's `2026.20655.2` experimental build string.
- Stated purpose (paraphrased from the thread): ML/tooling integration,
  version-control compatibility, and programmatic generation/validation —
  "straightforward JSON syntax so they can easily be edited and built using
  external tools." Planned schema files for external validation were also
  mentioned, not yet observed anywhere.
- **Hard compatibility warning**, from Derivative's own 2023.11170 changelog:
  *"Project .toe files saved in Experimental can not be loaded back in
  Official."* Unconfirmed whether that specific restriction still applies to
  the *text-format* mode specifically (vs. Experimental-vs-Official binary
  drift in general) — but it is the right prior until proven otherwise. See
  §5.

`file-structure: "single"` is a live setting with (by naming) at least one
sibling value implied — most plausibly a `"multi"` mode that splits a project
across multiple files (one per network/component), which would be the
obvious next step for real git diffability at scale. **Unconfirmed** — not
observed in any sample, not documented publicly. Worth deliberately testing
for once more experimental builds are available.

## 2. Schema, as observed in the sample

This is what actually exists on disk today, in this one build. Treat all of
it as **subject to change without notice** — there is no published schema
and no version guarantee beyond the per-substructure integers in `header`
(§2.6).

### 2.1 Top-level shape

No wrapper key. The root network's own children sit as top-level sibling
keys next to dot-prefixed metadata:

```
header            build + settings
.start            startup command script (§2.5)
.root             root network pane viewer state (pan/zoom)
.application      desktop/pane layout + window placement
project1          a root-level COMP  ┐
FNSTools          a root-level COMP  ├─ ordinary children of "/"
perform           a root-level COMP  │
local             a root-level COMP  ┘
```

The same shape recurses into every COMP: a COMP's own JSON object holds
`.node`/`.parm`(/`.cparm`/`.panel`/etc.) plus further sibling keys for its
own children. `FNSTools` in the sample is a genuine installed FNSTools root
(`.node`, `.cparm`, `.parm` — no children dumped in this excerpt), which
means this sample project already proves FNSTools survives a save/reload
through the text format.

### 2.2 A single operator

```json
"table1": {
  ".node": {
    "type": "DAT:table",
    "tile": [-450, 325, 130, 90],
    "flags": { "expose": false }
  },
  ".parm": { "defaultreadencoding": "cp1252", "rows": 1 },
  ".table": {
    "version": 1,
    "table": { "numRows": 1, "numCols": 4, "row0": { "...": "..." } }
  }
}
```

- `.node.type` — `"CATEGORY:opname"` (`COMP:base`, `DAT:text`, `CHOP:null`, …).
- `.node.tile` — `[x, y, w, h]`, replacing the binary format's separate
  `nodeCenterX/Y` + size fields.
- `.node.inputs` — **this is where wiring lives.** `{"0": "midiinmap"}` means
  input index 0 is connected to the sibling op `midiinmap`. There is no
  separate global wire list; connectivity is stored per-op, keyed by
  relative sibling name.
- `.node.color`, `.node.flags`, `.node.tags`, `.node.viewerSettings`,
  `.node.comment`, `.node.dict` — optional, present only when non-default.

### 2.3 Parameters — three modes, same shape as the binary format conceptually

```jsonc
"parentshortcut": "Project"                                   // constant
"fileFolder": { "mode": "expression", "value": "",
                "expression": "me.parent().fileFolder + ..." } // expression
"vc_name": { "mode": "bind", "defaultMode": "expression",
             "flags": { "readOnly": true }, "value": "",
             "bind": "op('./vc_data')[\"name\",1]" }           // bind
```

Custom parameters/pages live in a `.cparm` block (paired with `.customPars`
in `header.versions`), each entry carrying `type.style`, `label`, `page`,
`order`, `custHelp`, and clone-tracking via `"cloneState": "revise"/"immune"`.

### 2.4 DAT content — inline, not a file reference

```json
".text": {
  "version": 3,
  "table": { "contents": "\n'''Info Header Start\n...\nclass ExtTest:\n..." }
}
```

Text/table DAT contents are embedded directly as escaped JSON strings. In
`file-structure: "single"` mode there is no sign of any DAT deferring to an
external text file on disk — the whole project really is one file.

### 2.5 `externaltox` — unchanged in spirit

```jsonc
"externaltox": "modules/suspects/FNSTools/CustomParTools.tox"
// or, as an expression:
"externaltox": { "mode": "expression", "value": "",
  "expression": "me.parent().fileFolder + '/../../../Palette/FNSTools_ext/store/FNSTools.tox'" }
```

Externalized components are referenced exactly like a normal parameter,
constant or expression — same mechanism as the binary format today. The
referenced `.tox`'s *contents* are not duplicated into the JSON; only the
path/expression lives here. This means **today's `externaltox`-based
distribution model (packaging track, `shared`/`project` binding modes)
already maps directly onto the text format with no changes required.**

### 2.6 `.start` — global startup script, not a component manifest

```json
".start": {
  "commands": [
    "cookrate 60",
    "clock -f 1 -s 1 -o 0 -w 0",
    "realtime on",
    "viewers off",
    "resetaudioondevicechange off",
    "#expectednodes 446 40064"
  ]
}
```

Small, fixed project-level state (cook rate, clock config, a sanity-check
node-count comment) — not a list of default components. There is no
separate "this is what a blank new project contains" manifest anywhere in
the file; a project's top-level children just *are* whatever ops sit at the
root. The perform/root window is identified by a `COMP:window` op (here
named `perform`) whose `.parm.winop` points at the root network, plus a
`winplacement ... perform.path=/perform` command in `.application`.

### 2.7 Versioning

```json
"header": { "build": "2026.20655.2",
  "versions": { "color":1, "viewerSettings":1, "nodeFlags":1, "parDefault":4,
                "choiceList":1, "customPars":1, "range":1, "parList":1, "table":1 } }
```

Each sub-structure (color, table, customPars, …) carries its own version
integer independent of the overall build, and individual blocks
(`.table.version`, `.text.version`) echo the same numbers locally — implying
Derivative intends each piece to be independently migratable across
releases. This is the only forward-compatibility signal available; there is
no schema file to validate against yet.

### 2.8 Diff-friendliness and payload

Pretty-printed, tab-indented, one value per line, stable key ordering
throughout the ~15,600-line sample (spot-checked at multiple offsets) — a
single parameter edit should touch a handful of lines, not the whole file.
**Unconfirmed:** ordering stability across independent save cycles (would
need two saves of the same project diffed against each other — worth doing
before relying on this for any tooling).

No large embedded binaries. The only non-plain-text residue found: ~22 short
(under 130 chars) hex-encoded Python pickle blobs in `.node.dict` fields,
used for op `storage` — e.g. a pickled `{'texthash': '...'}`. No thumbnails,
no shader blobs, no base64 images anywhere in the sample.

## 3. What this means, in one paragraph

The format is genuinely text/JSON, genuinely diffable, and structurally
close enough to the binary format's own concept model (ops, `.parm`,
`externaltox`, custom pars) that nothing about FNSTools' current design
needs to change to be *compatible* with it. What it newly enables is
**editing a project's operator tree with a text editor or a script, without
TouchDesigner running at all** — see
[TextFormatInjectionStrategy.md](TextFormatInjectionStrategy.md) for what
that's worth to us and how risky it is to build on right now.

## 4. Open questions worth tracking

- Does a `"multi"` `file-structure` mode exist, and if so, does it split
  files at the COMP boundary (one file per component) or something else?
- Is key ordering actually stable across saves, or does it reshuffle?
- Does the Experimental→Official load restriction (§1) apply to
  text-format saves specifically, or was that a general binary
  Experimental-vs-Official warning that predates this feature?
- Are the planned external schema files public yet? (Not found as of this
  research pass.)
- Does `toeexpand`/`toecollapse` gain a mode that speaks this format
  directly, or does it stay a separate, older, undocumented ASCII dump?
