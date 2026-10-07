---
status: landed
summary: Highlight other creators' TouchDesigner tools on the website and in the picker, blog-style, with attribution. Builds on recommendations.json (link rows and pinned-tox rows already exist); adds post pages on the site, a Place button in the picker, and a third delivery kind for tdp Python packages.
since: 2026-09-25
---

# Community highlights

**The ask.** Present tools by other creators on the website and in the
installer, like a blog: each one gets a short write-up with clear credit.
Three kinds:

| Kind | Example | What a user can do |
|---|---|---|
| `link` | a Patreon post, a Gumroad page | read our write-up, open the author's page |
| `tox` | a .tox attached to a GitHub release | the above, plus place the exact file we checked |
| `tdp` | a tox shipped as a Python package (`tdp-` convention) | the above, plus install that exact version into the project's venv and place its tox |

## What already exists

- **`packaging/recommendations.json`** is the list, validated by
  `packaging/recommendations.py`. Rows need `name`, `author` and `url`.
  A row with `tox_url` + `sha256` + `bytes` can be placed; without them
  it is a link. Package-shaped fields (`version`, `requires`, `access`...)
  are refused, so the list can never be mistaken for our own packages.
  It publishes on its own (`upload.py --recommendations`), no release
  needed. The `tools` array is empty today.
- **The CMS** edits the list and pins a `tox_url` by hash.
- **The picker** shows the rows last, as "From other creators": a card
  with the author, the description and a link out. There is no Place
  button yet.
- **The updater** can already place a pinned row
  (`CommunityList`, `RefreshCommunity`, `PlaceCommunityTool`, files in
  `<store>/community/`). Nothing calls it from the picker.
- **The website shows none of it.**
- **Foreign packages** (TDXMap, ParHoverMIDI_VSN1) are a different thing
  and stay different: we mirror and update those. Highlights are never
  updated by us.
- **tdp** is supported by the launcher (TDXLPP `tdp.rs`, uv with pip
  fallback), not by FNSTools.

## Decided (2026-09-25)

- The section is `/community/`.
- Write-ups are Markdown and may be long, articles rather than blurbs.
- Authors are told before a highlight goes up; their images are used only
  with their permission.

## The plan

### 1. The data (recommendations.json, still schema 1)

The new fields are optional and additive. No reader checks the schema
number and every reader ignores fields it does not know, so the number
stays 1 and installs already in the field keep working.

Each row becomes a post as well as a card. New optional fields:

- `slug`: the page address, `[a-z0-9-]`.
- `date`: when we highlighted it; the site lists newest first.
- `image`: a screenshot, stored in our repo and used only with the
  author's permission.
- `platform`: `github`, `patreon`, `gumroad`, `itch`, `pypi`, or
  `other`. It picks the link label ("Get it on Patreon").
- `author_license`: the author's terms, as they state them, shown as-is.
  (`license` alone is refused: it is one of our package fields.)
- `tdp`: `{ "package": "tdp-foo", "module": "tdpFoo", "tox": "Foo",
  "lock": ["tdp-foo==1.2.0 --hash=sha256:...", ...] }`. The lock is every
  requirement the package resolves to, each at one version with its hash,
  written by the CMS pin. It plays the part `tox_url` + `sha256` plays for
  a tox: the exact set a curator checked. It is not update machinery.
  `tox` names an entry in the package's `_ToxFiles`, or is left out for a
  package with a single `ToxFile`.

The write-up is Markdown in `website/content/community/<slug>.md`, with
`name` in its frontmatter to join it to the row. A row without a write-up
still gets a card, with no post page.

### 2. The website (landed 2026-09-25)

- `/community/` lists every highlight, newest first: image, name, "by
  author", the kind (on their site, .tox file, Python package) and date,
  and the one-line description. A row with a `slug` links to its post; a
  row without one links straight to the author.
- `/community/<slug>/` is the post: title, byline with the author's link
  and the date, the image, then a credit box before the write-up (made
  by, their terms, the pinned file or package version, "Not part of
  FNSTools. <author> made it and maintains it; questions and support go
  to them.", and the button to their page).
- The landing page shows the three newest between the
  `<!-- COMMUNITY:START -->` / `<!-- COMMUNITY:END -->` markers, and
  nothing at all while the list is empty. Both footers link
  `/community/`; the header nav does not yet.
- The build refuses: a write-up with no row of that slug, a row with a
  slug and no write-up, a row `image` that is not in
  `website/content/community/images/`, and an image in a write-up that is
  not `/community/images/<file>` (posts sit one folder down, so a
  relative path would break).
- The pages sit outside `/docs/`, so the docs search does not index them.

**Drafts** (2026-09-26). A row with `draft: true` is still being written:
`recommendations.published()` leaves it out of what installs download, the
site build leaves it out of `/community/` and the landing strip, and its
write-up may exist without being an orphan. The CMS's Build site sets
`FNS_SHOW_DRAFTS=1`, so the local preview shows drafts marked "Draft"; the
public build never does, and the landing strip (committed in
`website/index.html`) never includes one. Untick Draft in the CMS to
publish. Frontmatter values containing a colon must be quoted; the build
names the file instead of crashing.

**Adding a highlight.**

1. Ask the author. Get their OK for the write-up and for any image.
2. Add the row to `packaging/recommendations.json` (or in the CMS):
   `name`, `author`, `author_url`, `url`, `description`, `slug`, `date`,
   `platform`, `author_license`, and `image` if there is one. For a tox,
   Pin it; for a Python package, fill `tdp` (step 5 adds the Pin for it).
3. Write `website/content/community/<slug>.md`. Frontmatter is optional:
   `title` (defaults to the row name) and `summary` (defaults to the
   description). Put pictures in `website/content/community/images/` and
   reference them as `/community/images/<file>`.
4. `python packaging/recommendations.py`, then `npm run pages` in
   `website/` to preview.
5. Publish the list to installs with
   `python packaging/upload.py --recommendations`, and the site with the
   usual website mirror and promote.

### 3. The console's Community view (landed 2026-09-25, moved 2026-09-26)

- **Community is its own place** (owner, 2026-09-26: at the bottom of the
  picker these read as more FNSTools tools). The console has a built-in
  **Community** tab after Updates (`ConsoleRegistryExt.BUILTIN_TABS`,
  order 30), listing the tools newest first. The picker lists none of them:
  one line, "N tools by other creators", switches the console to Community
  (`postMessage('fns:community')`), or opens the site's `/community/` when
  the picker is not inside the console (the installer's own window,
  `/get/`).
- **One copy of the card.** The card and its actions live in
  `packaging/configurator/base.js` as `window.fnsCommunity` (`card`,
  `load`), inlined by `sync_base.py` into the picker and the console page
  like the rest of the base. A card is never selectable. Its name opens our
  post when the row has one; chips open "our write-up" and the author's
  page ("on GitHub", "on Patreon"...), through `/open` when served (a Web
  Render ignores `target=_blank`).
- Served by the installer in TD, a pinned tox gets **place in this
  project**. The page POSTs `/community/place`; the installer resolves the
  working network (`PanePlacement`, the same rule `placement: pane`
  packages use, with its own rule, `CommunityLock`: /ui and /sys are refused,
  and so is the toolkit source, but an Embody-tracked network such as the
  project root is fine, because a placement only adds a component) and asks the
  updater, outside the request callback, to `PlaceCommunityTool`. The
  page polls `GET /community/place` (the updater's
  `communityPlaceResult()`) until it reads placed or failed.
- The updater checks size then hash before loading, as before, and now
  deletes a download that fails either check. One community download at a
  time; a second is refused with a message.
- The console forwards `/recommendations.json` and `/community/place` to
  the installer. Before this the console-hosted picker never showed the
  section at all.
- New highlights are not announced by the new-tools window. That window
  is for our tools.
- Verified in TD 2026-09-25 with a temporary list: a pinned tox placed
  into a scratch COMP, a wrong hash refused with the author named and its
  file deleted, a link-only row and an unknown name refused. The card
  flow (placing, placed) was checked on a stubbed page. Not yet tried:
  the real served picker clicking Place against a published row.

### 4. tdp installs (the largest piece)

**What is on PyPI (checked 2026-09-25).** Twelve projects start with
`tdp-`. Five are TouchDesigner tools, all by Wieland Hilker (plusplus.one):
`tdp-TauCeti` 5.1.16, `tdp-QrCodeCOMP` 1.0.0, `tdp-QrCode` 0.1.0,
`tdp-markdownrender` 0.0.1, `tdp-touchutilcollection` 0.8.0. The other
seven (datavisyn, Caleydo, Yitzchak Gale) are unrelated projects that
happen to share the prefix. So the prefix identifies nothing: every tdp
highlight is curated by name, and no list is built by searching.

**The convention, read from the wheels.**

- The importable module is `tdp<Name>` (`tdpTauCeti`, `tdpQrCodeCOMP`),
  or something else entirely (`touchutilcollection`). The row names it.
- A single-tox package exports `ToxFile`, a `pathlib.Path` to the tox
  inside the installed package.
- A package with several exports `_ToxFiles`, a name-to-path map
  (TauCeti: PresetManager, Tweener, PresetDashboard, PresetCuelist,
  PresetChopMapper, TweenCHOP).
- `__minimum_td_version__` states the oldest TD build. `tdp-touchutilcollection`
  is a library with no tox at all, so it is a dependency, never a
  highlight of its own.
- Packages have dependencies. `tdp-QrCodeCOMP` needs `qrcode[pil]` and
  `tdp-touchutilcollection`. A hash on the top package alone cannot
  install it, because `--require-hashes` demands a hash for every
  requirement. Hence the full lock in the row.

**The install.**

- The installer runs `uv pip install --require-hashes -r <lock>` into the
  project's venv (pip if uv is missing), as a subprocess, with no TD access
  from the worker. It then imports the module, resolves the tox and places
  it.
- A republished wheel no longer matches its hash and refuses to install.
  That is the same promise the `tox` rows make.
- The CMS pin refuses a lock that contains a package TD bundles (numpy,
  opencv and friends). Installing one of those into the venv is a known
  crash class.

**What the checks found (2026-09-25).**

- **TD's own manager.** `app.pyEnvHelper` (TDPyEnvManagerHelper, created at
  startup) links a venv before anything cooks when the .toe folder holds a
  `TDPyEnvManagerContext.yaml` or a `pyproject.toml`
  `[tool.touchdesigner.TDPyEnvManagerContext]`. The venv is
  `installPath/envName`, `./.venv` by default. `envPath`,
  `executablePath` and `sysPath` say what is linked. TD 2025.33070 runs
  Python 3.11.15. Docs: Palette:tdPyEnvManager, TDPyEnvManagerHelper.
- **The launcher (TDXLPP `tdp.rs`).** It reads the same context (pyproject,
  then yaml, then `.venv`-like folders). It never creates a venv itself:
  it drops the palette `tdPyEnvManager.tox`, whose activation shows
  Derivative's own disclaimer, which it deliberately does not bypass. It
  installs with uv (pip fallback) from outside TD, with no hashes and no
  check against TD's bundled packages. It finds the tox by importing the
  module's `ToxFile` in a venv subprocess, and places it with
  `externaltox` as the EXPRESSION `mod.<module>.ToxFile`, so the binding
  follows the package on any machine. It does not read `_ToxFiles`.
- **Embody** authors a minimal context yaml for its own uv venv, refuses
  URL/VCS/path specs and TD's bundled packages, and strips `VIRTUAL_ENV`
  and `PYTHONPATH` from child processes (tdPyEnvManager sets
  `VIRTUAL_ENV` process-wide).
- **TD's bundled packages** are in `sys.base_prefix + '/Lib/site-packages'`
  (numpy, requests, pyyaml, attrs, certifi, urllib3, packaging, ...). opencv
  and pyparsing ship without dist-info, so a dist-info scan misses them;
  Embody adds a seed list, and top-level folder names must be compared too.

**What landed (2026-09-26).** The proposal, as built:

- **Environment.** `FNS_Updater.PythonEnvStatus()` reads
  `app.pyEnvHelper` (`envPath`, `executablePath`). With none, Install
  answers `noenv` and the picker offers "set up a Python environment
  first": `SetUpPythonEnv()` drops the palette `tdPyEnvManager.tox` at `/`
  (unwrapped like a palette drag), switches it Active a couple of frames
  later, and presses Create vEnv. Switching Active shows Derivative's
  dialog, read from the tox on 2026-09-26: title "DISCLAIMER", "Sideloading
  Python environments and third party packages is at your own risk and can
  cause instabilities", buttons Continue / Abort. Abort stops there.
- **Install.** `InstallCommunityPackage(name, target)` refuses a lock
  naming a package TD ships (read from `sys.base_prefix`
  site-packages plus `TD_BUNDLED_SEED`), writes the lock beside the store's
  community list, and starts `uv pip install --python <venv> --require-hashes
  --only-binary :all: --no-deps -r <lock>` (the venv's pip with the same
  flags when there is no uv) with `VIRTUAL_ENV`, `PYTHONPATH`,
  `PYTHONHOME` and `PYTHONUSERBASE` removed. It is polled every 15 frames
  and killed after 10 minutes; its output is kept in `<name>.install.log`.
- **Place.** The venv's site-packages joins `sys.path` if it was not
  there, the module is imported, the tox is `_ToxFiles[tox]` or
  `ToxFile`, and the loaded COMP gets `externaltox =
  mod.<module>.ToxFile` (or the `_ToxFiles` entry) with
  `enableexternaltox` on. A module that was already imported says
  "Restart TouchDesigner to use the new version".
- **Routes.** `POST /community/install`, `GET`/`POST /community/pyenv`; the
  answer is read from `GET /community/place` like a tox placement. The
  console forwards all of them.
- **Pin.** `packaging/tdp_pin.py` (the CMS "Pin" beside the package name)
  reads the newest release's wheel for the module and its toxes, compiles
  the universal hashed lock for Python 3.11, and refuses a bundled package.
  `tdp.also` lists what a package imports without declaring it; it joins
  the lock and is kept so a re-pin remembers it.

**Unpinned since 2026-09-27** (owner: no versions to keep updating). A
`tdp` row now names the package, its module, the tox and `also`; a `lock`
is refused. The installer runs a dry run first (`uv pip install --dry-run`,
or pip's `--dry-run --report`), refuses when the result would add a package
TouchDesigner ships, and then installs the latest release, wheels only.
`tdp_pin.py` became the curator's check (module, toxes, what it resolves
to today, the same refusal), the CMS button reads "Check", and the post
says "its latest release". Verified in TD against a scratch venv: `also:
opencv-python` refused (numpy, opencv-python) with nothing installed;
TauCeti + touchutilcollection dry-run, installed, TweenCHOP placed with no
errors. What this gives up: a user gets whatever the author published last,
not the version the curator looked at.

**Found on the way.** `tdp-TauCeti` 5.1.16 imports `touchutilcollection`
in its TweenCHOP extension but does not declare `tdp-touchutilcollection`.
Pinned from its own metadata, it installs and places a TweenCHOP whose
extension fails to import. With `also: ["tdp-touchutilcollection"]` it
places cleanly. Worth telling the author.

**Verified** in TD 2025.33070 on 2026-09-26 against a scratch venv made
with TD's Python (never the project's own `.venv`): that install and
placement, the numpy refusal, and the `noenv` answer. The picker flow
(install, set up environment, install, placed) ran on a stubbed page.
**Not yet run:** `SetUpPythonEnv()` itself (it would drop the manager into
this project and raise the dialog), and a served picker against a
published row.

### 5. The CMS (landed 2026-09-25, except the tdp Pin)

- The Community editor gives each row two folding sections. **Website
  post:** slug (with "From name"), date, platform, the author's terms, an
  image picked from `website/content/community/images/` or uploaded
  there, and the write-up in Markdown with "Start one" and a preview.
  **Python package:** package, module, tox, and the lock, pasted as
  `uv pip compile --generate-hashes` prints it.
- Save writes the list and the write-ups as one step, and checks
  everything first: an invalid row, a slug with no write-up or a rename
  onto an existing write-up leaves every file as it was. A changed slug
  renames the write-up. A write-up whose row is gone moves to
  `website/content/community/archive/` with a timestamp; nothing is
  deleted.
- An upload is named after the row's slug, never overwrites a file, and
  is capped at 8 MB.
- The tdp Pin landed with step 5 (section 4).

## Built with TDFam (2026-09-28)

A section of `/community/`, linkable as `/community/#tdfam`, listing
operator families made with TDFam. Its rows are `families` in
`packaging/recommendations.json`, edited in the CMS's Community editor
under "Built with TDFam", and validated by both validators like the
tools (name, author and url required; url https or a page on this site;
`ops` a positive whole number; `tool` must name a row in `tools`; `ours`
true or false). Installs never download it: `published()` leaves it out.

A card opens its `tool`'s post when that post is published, else the
family's own url. `ours` marks the FNS family: its operator count is
counted at build from the manifest's family members, leaving previews
out, so it follows the releases. The first two: FNS (links
`/docs/fns-opfamily/`) and T3D (48 operators, opens the T3D post).

## Attribution rules

- The author's name and link on every card and post, above the fold.
- Their license text, unedited.
- Their images only with their permission; otherwise no image.
- Nothing suggests we made it, support it or update it.
- Tell the author before publishing a highlight.

## Order of work

1. The new fields and both validators, with tests. (Landed 2026-09-25.)
2. Website `/community/` and post pages, landing strip. (Landed 2026-09-25.)
3. CMS fields and write-up editor. (Landed 2026-09-25.)
4. Picker: Place for `tox` rows, post links. (Landed 2026-09-25; ships with the next release.)
5. tdp install. (Landed 2026-09-26; ships with the next release.)
