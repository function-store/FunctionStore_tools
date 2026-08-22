---
package: FNS_Console
summary: 'The toolkit''s web front: one page served from inside your project, with a tab per concern -- settings, install & remove, and whatever your tools contribute.'
features:
  - name: Opening it
    anchor: opening-it
  - name: The tabs
    anchor: the-tabs
  - name: How it runs
    anchor: how-it-runs
  - name: Contributing a tab
    anchor: contributing-a-tab
  - name: Worked example -- ColorUI
    anchor: worked-example-colorui
  - name: HTTP API
    anchor: http-api
  - name: Python API
    anchor: python-api
  - name: Developing on it
    anchor: developing-on-it
  - name: Troubleshooting
    anchor: troubleshooting
---

The console is the one place to look at and steer an installed toolkit
from a browser: every tool's settings on a single scrollable page, the
install picker, and any tab a tool decides to contribute. It is served
from inside your project on `127.0.0.1`, only while you are looking at it,
and it holds no tool knowledge of its own -- every request is routed to
the component that owns the answer.

## Opening it

From the toolkit root's `FNSTools` parameter page:

| Pulse | Lands on |
|---|---|
| **Open Settings** | the *Settings* tab |
| **Pick Tools** | the *Install & remove* tab |

From the `FNS_Console` component itself: **Open Console**. From Python:

```python
op.FNS_CONSOLE.Open()                 # Settings
op.FNS_CONSOLE.Open(tab='tools')      # Install & remove
op.FNS_CONSOLE.Open(tab='ColorUI')    # a contributed tab, by canonical name
op.FNS_CONSOLE.Open(panel=False)      # force the system browser
```

It shows in the toolkit root's `webBrowser` panel when the root has one
(the bootstrap ships one), else in your system browser. The panel handles
everything the page does, file dialogs included. The tab is the URL
fragment (`#settings`, `#tools`, `#t-<name>`), so a reload keeps it and a
link can deep-link to it.

## The tabs

- **Settings** -- every registered tool as a section card (sticky header,
  parameters grouped by page), a jump list with scroll-spy on the left,
  search across all tools. Writing a value goes through
  `FNS_ConfigRegistry`'s own filters and persistence, so the page can
  never disagree with the components. The header carries **scope**
  (global/project -- see FNS_ConfigRegistry), **Export** (writes
  `<config dir>/exports/FNStools_config_<stamp>.json` server-side and
  offers a download) and **Import** (applies a document to installed tools
  now and keeps sections for tools you install later).
- **Install & remove** -- the `FNS_Installer` picker, served through the
  console. Unchecking an installed tool removes it; its settings are kept
  for the next install. Installing decides *what is in the project*; the
  config layer always re-applies on top. In the toolkit's own source
  checkout this tab is locked (it would remove authored masters).
- **Contributed tabs** -- anything a tool registers (below). They sit
  after a divider, sorted by their declared order; the two built-ins are
  the console's own and always shown.

### Exposure: shipped dormant, enabled by the install

Every tool artifact ships with **Expose to Console off**, and the
toolkit's installer turns it on as it lands the package. One artifact
therefore serves two lives:

| How the tool arrived | Console exposure | Its own panel |
|---|---|---|
| dropped into a project on its own (a standalone plugin) | off -- nothing raises a console | works as always |
| installed by `FNS_Installer` (bootstrap, picker, Textport rail) | **on**, flipped once at install | off while exposed -- the console is the UI |
| updated by `FNS_Updater` | untouched -- your choice persists | follows your choice |

Why not simply ship it on: a registry host bootstraps its own `/sys`
global when none exists, which is right for a toolbar button (it *adds*
a capability) and wrong for the console, whose exposure *removes* a local
surface. A standalone ColorUI shipped exposed would raise a console nobody
asked for and switch off its own panel. The rule, for any future surface
with that property: *a host whose exposure takes a local surface away
ships dormant and is enabled by the install rail, never by bootstrapping
itself.*

The flag is the tool's own **Expose to Console** parameter (its Registry
page), which the config registry persists -- so after the install's one
decision, your choice roams across projects and survives updates. If you
drag a toolkit package into a project by hand instead of installing it,
it arrives in local mode: flip Expose on the tool's page.

### Managing tabs

The **⋯** button at the end of the tab bar lists every contributed tab,
hidden ones included, with a show/hide checkbox. The choice is written
back to the contributing tool's **Shown in Console** parameter, so it
persists with the tool and roams with its Registry page like any other
setting -- the console keeps no list of its own. A tool decides its own
default the same way, and can stay out of the console entirely (below).

## How it runs

`FNS_Console` is a registry in the FNS sense (it sits on `RegistryBase`
like the toolbar, navbar and config registries):

- The in-project master `FNSTools/FNS_Console` promotes a global copy to
  `/sys/FNS_Registries/FNS_Console`, reachable as `op.FNS_CONSOLE`. The
  global is the API owner; the master and every host forward to it.
- **The surface is the server.** The global owns a Web Server DAT
  (`console_server`) that is created on demand, bound to the first free
  port in **36710-36759**, switched on by `Open`, and switched off after
  **ten idle minutes**. It is never saved into the `.toe` or any package
  -- `/sys` is rebuilt on every project open. Several open projects each
  run their own console on their own port.
- The page (`console_page`) and the request dispatcher
  (`console_server_callbacks`) ride along from the master; the global
  pulls them from the master if a promoted copy predates them.
- Routing: `/api/*` goes to `FNS_ConfigRegistry`'s `Ui*` methods (the
  paths are the registry's original ones -- the TDXLPP launcher reads
  `/api/state` and `/api/set`); `/tools` and the picker's endpoints go to
  `FNS_Installer.ServeRequest`; `/t/<tab>/...` goes to the tool that
  contributed the tab. Without the config package the Settings tab says
  so; without an installer the Install tab says so.
- Everything is `127.0.0.1` only.

## Contributing a tab

A tool contributes a tab the same way it contributes a toolbar button or
its settings: it carries a stamped **`FNS_Console` host**. The host's
Registration page:

| Par | Meaning |
|---|---|
| **Tool COMP** | the contributing tool; defaults to the parent (the host lives inside the tool) |
| **Canonical Name** | URL-safe (letters, digits, `_ -`); the tab lives at `/t/<name>/`. Empty = the tool's name |
| **Tab Page** | a text DAT holding the tab's HTML. Served **verbatim** in an iframe under `/t/<name>/` |
| **Tab API** | optional Python DAT defining `onConsoleRequest(action, method, body)` |
| **Local Browser** | optional: the tool's own web browser panel rendering the same page. While the tab is exposed the console serves the page and **switches that browser's `Active` off** -- a renderer nobody looks at would keep a CEF process and a texture alive -- and switches it back on when exposure ends (Expose off, a failed registration, the host removed). A tool that wants finer control implements `OnConsoleExposure(exposed)` on its extension; the host then calls that instead of touching `Active` |
| **Expose to Console** (Auto-register) | the tool's own decision: on = publish the tab while the component exists; **off = local only** -- the tool keeps its own interface and contributes nothing |
| **Register / Status** | publish once regardless of Expose; read-only status |
| **Shown in Console** (Displayed) | on the bar or hidden. The console's tab manager writes here, so a user's show/hide persists with the tool |
| **Tab Label / Tab Order** | what the tab bar shows, and where. Built-ins sit at 0 and 10; contributions default to 50 and sort by order, then label |

These are mirrored onto the tool's own **Registry** page (prefix `Cs`),
so a tool like ColorUI exposes, hides or goes local-only from its own
parameters without anyone opening the host.

Two rules that follow from how it is served:

1. **The page is self-contained.** Inline its CSS and JS -- there is no
   asset route. Relative URLs resolve under `/t/<name>/`, so `fetch('api/x')`
   reaches your API; a root-relative `/api/...` would reach the
   *console's* API instead.
2. **DAT parameters take sibling names.** An OP parameter resolves from
   the host's parent network, i.e. the tool. Write `webui_html`, not
   `../webui_html` (that looks one level too high).

The API DAT's single function:

```python
def onConsoleRequest(action, method, body):
    """action = the path after /t/<name>/api/, method = 'GET'|'POST',
    body = parsed JSON of a POST, else None. Return anything JSON-able."""
```

What a tool contributes is a **web re-expression of what it owns** --
tables, parameters, state -- talking to the same extension its panel
talks to. A TouchDesigner panel itself cannot be embedded in a browser.

Stamping the host from Python (the master does the copy safely):

```python
op.FNS.op('FNS_Console').ext.ConsoleRegistryExt.StampHost(
    op.FNS.op('MyTool'), canonical_name='MyTool', autoregister=True,
    par_values={'Tabpage': 'my_page', 'Tabapi': 'my_api',
                'Tablabel': 'My Tool', 'Taborder': 30})
```

Or register directly, without a host, from your own extension:

```python
op.FNS_CONSOLE.RegisterTab(comp, 'MyTool', page=op('my_page'),
                           api_dat=op('my_api'), label='My Tool', order=30)
```

A direct registration is ephemeral (the global is rebuilt every open);
re-register on your `onStart`. A host re-publishes itself.

## Worked example -- ColorUI

ColorUI's panel already *is* a web page (`webui_html`, rendered in its own
Web Render browser, talking to TD through `document.title` rewrites up
and `executeJavaScript` down). Its console tab is **the same page** with
a second transport, picked at load:

```js
const SERVED = /^https?:$/.test(location.protocol);
const Bridge = SERVED ? HttpBridge : TitleBridge;   // same post()/ack() surface
```

Served, `HttpBridge` POSTs every command to `api/cmd` and gets the fresh
state back, and polls `api/state` every two seconds so edits made in the
in-TD panel show up. The extension side is two methods over the code the
panel already used:

```python
def ConsoleState(self):
    return {'ok': True, 'state': self._statePayload()}

def ConsoleCommand(self, msg):
    self._toast_sink = []            # toasts a command raises ride back
    try:
        self._dispatch(msg)          # the title bridge's vocabulary
    finally:
        toasts, self._toast_sink = self._toast_sink, None
    return {'ok': True, 'state': self._statePayload(), 'toasts': toasts}
```

and the whole `console_api` DAT:

```python
def onConsoleRequest(action, method, body):
    ext = parent.ColorUI.ext.ExtColorUI
    if action == 'state':
        return ext.ConsoleState()
    if action == 'cmd' and method == 'POST':
        return ext.ConsoleCommand(body)
    return {'ok': False, 'why': 'unknown action: %s %s' % (method, action)}
```

Host pars: Tab Page `webui_html`, Tab API `console_api`, Local Browser
`webBrowser`, label `ColorUI`, order 20.

ColorUI goes one step further and keeps its renderer off **whenever
nobody can see it**: a Panel Execute DAT (`watch_viewer`) on the panel
value `winopen` -- "1 if panel is open as a floating window" -- feeds
`SyncLocalBrowser`, whose single rule is *Active = viewer open AND not
served by the console*. The console's hand-off (`OnConsoleExposure`)
and the Expose parameter call the same rule, so there is one owner and
no flicker. Consequences: with the viewer closed the Web Render cooks
nothing at all; *Open UI* opens the console's tab while served, else the
panel (and the renderer with it); JavaScript pushes and reload-kicks are
skipped while the renderer is off.

## HTTP API

All on the console's port, `127.0.0.1` only.

| Route | Method | Answers with |
|---|---|---|
| `/` | GET | the console page |
| `/api/tabs` | GET | `{ok, tabs:[{name, label, order, builtin, displayed, url?, api?, source?}]}` -- hidden contributions included |
| `/api/tabs/display` | POST `{name, displayed}` | `{ok, name, displayed, persisted}`; built-ins refuse |
| `/api/state` | GET | every registered tool with its exposed parameters (+ `scope`, `project`, `installer`) |
| `/api/set` | POST `{tool, par, value}` | `{ok, val}` -- validated against what `/api/state` exposes |
| `/api/export` | GET | `{ok, document, tools, saved_to}` -- the document is also written to `<config dir>/exports/` |
| `/api/import` | POST (a config document) | `{ok, applied:[...], deferred:[...], scope}` |
| `/api/scope` | GET / POST `{value, mode}` | `{ok, scope}`; `global` requires `mode` `push` or `adopt` |
| `/tools`, `/manifest.js`, `/selection`, `/status`, `/install` | — | forwarded to `FNS_Installer` |
| `/t/<name>/` | GET | the contributed tab's page |
| `/t/<name>/api/<action>` | GET / POST | the tab's `onConsoleRequest` |

## Python API

On `op.FNS_CONSOLE` (any host or the master forwards):

| Call | Does |
|---|---|
| `Open(tab=None, panel=True)` | serve + show; returns `{ok, url, shown}` |
| `Close()` | stop serving now |
| `Url()` | the URL while serving, else `None` |
| `Tabs(include_hidden=False)` | the ordered tab list; hidden contributions only when asked |
| `SetTabDisplayed(name, bool)` | show/hide a contribution, written back to its host's Displayed par |
| `RegisterTab(comp, name, page=, api_dat=, label=, order=, displayed=True)` / `UnregisterTab(name)` | contributions without a host |
| `ServeTab(name, subpath, method, body)` | what the dispatcher calls for `/t/...` |

`op.FNS_CONFIGREGISTRY.OpenSettingsUI(tab, panel)` still works -- it
forwards here.

## Developing on it

- Sources are Embody-externalized under `FNSTools/FNS_Console/`
  (`ConsoleRegistryExt.py`, `console_server_callbacks.py`,
  `console_page.html`, `pre_release.py`). A disk edit hot-syncs into the
  master **and** into the `/sys` global (its DATs keep the file binding),
  so the running console picks it up on the next request -- reload the
  page.
- Structural changes under `FNSTools` (a new host, a new DAT) must be
  persisted the project's way or a reload reverts them: `pi.Add` for new
  components, `pi.Save` on the changed suspects, **`pi.Save(op.FNS)`
  last**, then save the project.
- Promoted globals live in `/sys/FNS_Registries`; a `findChildren` from
  `/` does not descend there -- search that container explicitly.
- The pre-release hook scrubs registration state, the shortcut, cloning,
  the external-tox binding and any server DAT, so a shipped `FNS_Console`
  is inert until it promotes in the user's project.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| "no free port in 36710-36759" | fifty consoles open, or that block is reserved on the machine (`netsh interface ipv4 show excludedportrange protocol=tcp`); close some, or change `UI_PORTS` |
| Page stops answering after ~10 minutes | by design -- the server idles out; pulse Open again |
| Settings tab says the config package is missing | `FNS_ConfigRegistry` is not installed or not yet promoted |
| Install tab says there is no installer | the project has no `FNS_Installer`; drop the bootstrap or the bare installer |
| Install tab shows **Locked (source checkout)** | you are in the toolkit's own source root; point *Install Into* at a scratch container |
| A contributed tab is missing | host status shows why (`Registration Status`): no page DAT, a name that is not URL-safe, or a name clashing with a built-in. Remember sibling names for the DAT pars |
| A tab's `fetch('/api/...')` hits the wrong thing | root-relative paths reach the console; use relative `api/...` |
| Register pulse "did nothing" in a script | parameter callbacks fire at frame end -- read the status on the next frame |
