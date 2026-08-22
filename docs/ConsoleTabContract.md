---
status: in-force
summary: What a tool must do to publish a tab into the FNS_Console web front -- RegisterTab, the api DAT contract, and the rejection rules.
since: 53eb4ed 2026-08-22
verified: 2026-08-22 — ColorUI is the first contributor (479e76d); tab manager + dormant exposure (d71da5f, 63d6e3a)
skill: fns-registry
---

# Contract: contributing a tab to FNS_Console

What a tool must do to publish a tab into the toolkit's web console. Source of
truth: [ConsoleRegistryExt.py](../FNSTools/FNS_Console/ConsoleRegistryExt.py)
(`RegisterTab` L282, `_validateTab` L141, request dispatch L405). The registry
pattern this sits on is [RegistryScheme.md](RegistryScheme.md); the promoted
global lives per [RegistryHomeContract.md](RegistryHomeContract.md).

> Rescued 2026-08-22 from `briefs/2026-08-22-fns-console.md` (gitignored). The
> signature sketched in that brief — `RegisterTab(comp, name, label, page_dat,
> api_dat, order)` — never shipped. **This file is written from the code.**

## 1. The shape

A tab is a **contribution**, like every other surface in the toolkit. The tool
carries a stamped `FNS_Console` host whose Registration pars name:

- a **page DAT** — a text DAT served verbatim in an iframe under `/t/<canonical>/`;
- optionally an **api DAT** — its module answers `/t/<canonical>/api/<action>`.

What you contribute is a *web re-expression* of what your tool owns — tables,
parameters, state. **Never a TD panel**: a browser cannot host one.

## 2. The call

```python
op.FNS_CONSOLE.RegisterTab(comp, canonical, page=None, api_dat=None, label='',
                           order=50, displayed=True, source_registry=None)
```

| Arg | Meaning |
|---|---|
| `comp` | the tool COMP that owns the tab (stored by path **and** id) |
| `canonical` | URL-safe id — letters, digits, `_`, `-`. Becomes `/t/<canonical>/` |
| `page` | text DAT, served as-is. Required |
| `api_dat` | optional; its module must define `onConsoleRequest` |
| `label` | display name; defaults to `canonical` |
| `order` | bar position, default 50 (built-ins are 0 and 10) |
| `displayed` | `False` registers the tab **hidden** — present in the tab manager, off the bar, until someone shows it |
| `source_registry` | optional provenance for the healing sweep |

Call it on the global (`op.FNS_CONSOLE`) — guarded, since no registry is
guaranteed to exist:

```python
console = getattr(op, 'FNS_CONSOLE', None)
if console is not None and hasattr(console, 'RegisterTab'):
    console.RegisterTab(me.parent(), 'colorui', page=me.parent().op('console_page'),
                        api_dat=me.parent().op('console_api'), label='ColorUI')
```

A host that is not the `/sys` global forwards to the global through
`_registryApi()`; with no global ready the call is a logged no-op, never an
error. `UnregisterTab(canonical)` removes it (aliased `UnregisterPanel`, which
is the name RegistryBase's host teardown calls).

## 3. Rejection rules (`_validateTab`)

Registration is refused, with a `debug()` line and no exception, when:

- `comp` is None, or `canonical` is empty;
- `canonical` is not URL-safe after stripping `_` and `-`;
- `canonical` collides with a **built-in**: `settings`, `tools`. Settings and
  Install & remove are built in, not registrations;
- `page` is None, or is not a text DAT (`hasattr(page, 'text')`).

## 4. The api DAT

```python
def onConsoleRequest(action, method, body):
    """action: the path after /t/<canonical>/api/ ; method: GET/POST ;
    body: parsed request body. Return JSON-able data (None -> {'ok': True})."""
```

Dispatch guarantees, all from L413-L429:

| Situation | Response |
|---|---|
| no api DAT registered | 404 `tab has no api DAT` |
| DAT fails to compile | 500 `api DAT failed to compile: <e>` |
| no `onConsoleRequest` | 404 `api DAT defines no onConsoleRequest` |
| handler raises | 500 with the exception text |
| handler returns `None` | 200 `{'ok': True}` |

Your handler runs **on the main thread while a request is in flight** — keep it
cheap, same spirit as the "handlers must be quick" rule everywhere else. Both
the page DAT and the api DAT are resolved **by id first, then path**, so a
renamed or moved DAT survives; a deleted one yields 404 `tab page DAT is gone`.

## 5. Your own browser goes quiet

If your tool's panel is a Web Render of the same page (ColorUI is), name it on
the host's `Local Browser` par. While the console serves the page, the host
switches that renderer's `Active` **off** — it would burn a CEF process and a
texture for nobody — and back on when the exposure ends (Expose off, a failed
registration, or the host going away). Compare-before-set, so a plain re-apply
does not flicker.

## 6. Nothing here is durable

The console's Web Server DAT lives on the `/sys` global, is created on demand,
activated by `Open`, and deactivated after the idle timeout. `/sys` is rebuilt
on every project open, so **registrations must be re-made on init** — like every
other registry surface. Several open projects each run their own console on the
first free port of `UI_PORTS`.
