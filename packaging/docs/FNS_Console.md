# FNS_Console

The toolkit's web front: one page, served from inside your project on
`127.0.0.1`, with a tab per concern.

- **Settings** — every installed tool's persisted parameters on one
  scrollable page, config export/import, and the global/project scope
  switch. Backed by `FNS_ConfigRegistry`.
- **Install & remove** — the `FNS_Installer` picker. Unchecking an
  installed tool removes it; its settings are kept for the next install.
- **Contributed tabs** — any tool can add one (below).

Open it from the toolkit root's `FNSTools` page: **Open Settings** (Settings
tab) or **Pick Tools** (Install & remove), or from the `FNS_Console`
component's **Open Console** pulse. It shows in the root's `webBrowser`
panel when there is one, else in your system browser.

## How it runs

`FNS_Console` is a registry in the FNS sense: the in-project master
promotes a global copy to `/sys/FNS_Registries/FNS_Console`
(`op.FNS_CONSOLE`), and that global owns a Web Server DAT that exists
only while the page is in use — created on demand, bound to the first free
port in **36710-36759**, switched off after ten idle minutes, never saved
into the `.toe` or any package. Several open projects each run their own.

The console holds no tool knowledge. `/api/state`, `/api/set`,
`/api/export`, `/api/import`, `/api/scope` go to the config registry;
`/tools` and the picker's endpoints go to the installer; a contributed tab's
traffic goes to the tool that contributed it.

## Contributing a tab

A tool contributes a tab by carrying a stamped `FNS_Console` host (the same
way it carries a toolbar or config host). On the host's Registration page:

| Par | Meaning |
|---|---|
| `Tool COMP` | the contributing tool (defaults to the parent) |
| `Canonical Name` | URL-safe name; the tab lives at `/t/<name>/` |
| `Tab Page` | a text DAT holding the tab's HTML, served verbatim in an iframe — inline its CSS/JS |
| `Tab API` | optional Python DAT defining `onConsoleRequest(action, method, body)` → JSON-able; answers `/t/<name>/api/<action>` (`body` = parsed JSON of a POST, else `None`) |
| `Tab Label` / `Tab Order` | what the tab bar shows, and where (built-ins sit at 0 and 10; contributions default to 50) |

What a tool contributes is a web re-expression of what it owns — tables,
parameters, state — talking to the same extension its panel talks to. A
TouchDesigner panel itself cannot be embedded in a browser page.

From Python: `op.FNS_CONSOLE.RegisterTab(comp, name, page=dat, api_dat=dat,
label=..., order=...)`, `UnregisterTab(name)`, `Tabs()`, `Open(tab=,
panel=)`, `Close()`, `Url()`.

### Worked example: ColorUI

ColorUI's panel already *is* a web page (`webui_html`, rendered in its own
Web Render browser, talking to TD through `document.title` rewrites and
`executeJavaScript`). Its console tab is **the same page** with a second
transport: when served over http it POSTs its commands to
`/t/ColorUI/api/cmd` and polls `/t/ColorUI/api/state` every two seconds;
inside the panel nothing changed. The host's pars: `Tab Page` =
`webui_html`, `Tab API` = `console_api` (a 12-line DAT that hands `state`
and `cmd` to `ExtColorUI.ConsoleState` / `ConsoleCommand`), label
`ColorUI`, order 20. Note the DAT paths are **bare sibling names** — an OP
parameter resolves from the host's parent network, so `../webui_html`
would look one level too high.
