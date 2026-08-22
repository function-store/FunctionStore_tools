---
status: in-force
summary: 'Manual port guide handed to the TDFam repo: replacing its fire-and-forget mainmenu copy with a MainMenuRegistry-managed entry. External deliverable.'
since: 4022dc4 2026-08-13
---

# TDFam × MainMenuRegistry — manual port guide

Port of the live prototype (verified 2026-08-12 in FunctionStore_tools_2025_DEV)
that replaces TDFam's fire-and-forget `OpFamUI` copy in `/ui/dialogs/mainmenu`
with a **MainMenuRegistry-managed entry**: ordered/showable from the FNS
Main Menu Configurator, healed by the registry watch tick, and fully
backwards-compatible with projects that have no FNS tools installed.

Two deliverables sit next to this file:

- **`TDFam_MainMenuRegistry_host.tox`** — the configured host component,
  exported portable (no external file references, no clone binding, no
  Embody metadata). This is the only new component TDFam ships.
- This document — one component drop + one function patch.

---

## 1. What goes where (summary)

| # | Change | Where in the TDFam repo |
|---|---|---|
| 1 | Drop `TDFam_MainMenuRegistry_host.tox` as a child named **`MainMenuRegistry`** INSIDE the **`OpFamUI`** component | the TDFamRegistry master (wherever `TDFamRegistry/OpFamUI` is authored — it propagates into the nested template in `TDFam_create` and into every shipped copy from there) |
| 2 | Patch **`get_or_create_famui_manager`** in `GlobalUIInjector` | the GlobalUIInjector DAT/module of TDFamRegistry |
| 3 | (nothing else — no other TDFam code touches the mainmenu path) | |

Design shape (matches the FNS registry scheme's "host lives INSIDE the
component it registers"): the host sits in `OpFamUI` with `Comp = ..`, so it
registers the very panel it lives in. It is present in every TDFamRegistry
copy; the one that rides to `/sys` on promotion is automatically neutralized
by the scheme's `/sys`-guard (its `Regstatus` reads `Skipped (/sys or /ui)`)
— that is correct and expected. Registration always comes from the
network-side copies (the nested template inside each family comp, and the
dev master), which is exactly the redundancy you want: any one live copy
keeps the FAM button alive; healing re-registers from a survivor if the
current publisher dies.

---

## 2. The host component (deliverable 1)

`TDFam_MainMenuRegistry_host.tox` is a copy of the FNS `MainMenuRegistry`
(v0.1.0, `RegistryBase`-based) already configured for TDFam. If you prefer to
configure a fresh copy from the FNS_MainMenu package instead, these are the
exact values (Registration page, everything else at defaults):

| Par | Value | Why |
|---|---|---|
| `Comp` | `..` (constant, the default) | registers the OpFamUI panel the host lives inside |
| `Canonicalname` | `OpFamUI` | the entry name in the global registry (and the mirror name: `mmitem_OpFamUI`) |
| `Callback` | empty | no lifecycle hooks needed |
| `Autoregister` | **On** | publishes whenever this copy initializes outside `/sys` |
| `Menuorder` | `-1` | default append within the side band |
| `Align` | **`right`** | places the mirror in the right band — between the stretchy status area and the right corner, i.e. next to the Configurator gear, where the legacy copy sat |
| `Anchor` | empty | side band is sufficient; no pin to a named stock item |
| `Displayed` | On | |
| `Barwidth` | `0` | mirror width live-follows the source panel (45 px) |
| `Helpurl` | empty (or your wiki page — shows on right-click in the Configurator) | |
| `Promotepars` | **Off** | deliberate: don't grow a bound `Registry` page on the OpFamUI panel comp |
| `clone` | **empty**, `enablecloning` Off | ship clean. In projects that carry the FNS MainMenu package, the FNS global's healing tick re-binds the clone automatically (`_healHostClones`); everywhere else the host is standalone and updated by TDFam's own updater |
| COMP `externaltox` | empty, `enableexternaltox` Off | **critical** — an inherited externaltox on a copied host reloads the WRONG tox into it at boot (hazard paid for during the FNS port) |
| tags | `FNS_MainMenuRegistry` only | findability convention; do NOT let it inherit `pi_suspect` or any tracker tag from your pipeline |

Also embedded in the tox: `MainMenuRegistryExt`, `RegistryBase`,
`callbacks_template`, `pre_release`, `ExtUtils` — all with file bindings
stripped (text embedded), so nothing dangles in the TDFam repo. Leave them
that way; do NOT re-bind `RegistryBase` to a file unless you adopt the FNS
shared-file workflow.

**Placement inside OpFamUI**: anywhere clear in the network (the prototype
put it below the existing children's bounding box). It has no wires.

**What the host does on init** (so you know what "working" looks like):
outside `/sys` it installs/updates the `/sys/MainMenuRegistry` global if the
FNS package isn't already providing one (the host IS the bootstrap — TDFam
works in a bare project with zero FNS tools), then registers `OpFamUI`.
The global then builds `mmitem_OpFamUI` (a selectCOMP mirror of the panel,
height-enforced to the bar's 19 px, width following the source) wired to the
bar's `emptypanel`, and heals it every ~2 s watch tick. Two or more TDFam
copies registering the same canonical is benign — the entries are
equivalent, last writer wins, healing keeps one mirror.

---

## 3. The code patch (deliverable 2)

`GlobalUIInjector.get_or_create_famui_manager` currently copies the OpFamUI
template into `/ui/dialogs/mainmenu` unconditionally. Gate it on the
registry entry so the two mechanisms can never double-inject, and prune the
legacy copy when the registry takes over. Replacement for the whole function
(current body: the `ui_manager_path = '/ui/dialogs/mainmenu/OpFamUI'`
version; only the marked block is new):

```python
	def get_or_create_famui_manager(self, force=False):
		"""Get or create the central OpFamUI manager.

		When the MainMenuRegistry global is present and carries our
		'OpFamUI' entry (published by the host inside the OpFamUI
		template), the bar is the registry's responsibility: it mirrors,
		orders and heals the panel. In that case this routine only PRUNES
		the legacy injected copy and stands down. Projects without the
		registry keep the legacy injection path unchanged.
		"""
		ui_manager_path = '/ui/dialogs/mainmenu/OpFamUI'
		ui_manager = op(ui_manager_path)

		# --- NEW: MainMenuRegistry takeover gate -------------------------
		mmreg = getattr(op, 'MAINMENUREGISTRY', None)
		if mmreg and mmreg.valid and mmreg.extensionsReady:
			try:
				if 'OpFamUI' in mmreg.Widgets:   # registered -> registry owns the bar
					if ui_manager:               # retire the legacy copy once
						ui_manager.destroy()
					return None
			except Exception as e:
				debug(f'OpFamUI registry gate failed, using legacy path: {e}')
		# ------------------------------------------------------------------

		internal = self.ownerComp.op('internal_pars')
		if internal:
			force = force or internal.par.Force.eval()
			local_dev = internal.par.Dev.eval()
		else:
			local_dev = False

		if (force or local_dev) and ui_manager:
			ui_manager.destroy()
			ui_manager = None

		if not ui_manager:
			template = self.ownerComp.op('OpFamUI')
			if local_dev:
				template = self.ownerComp.op('OpFamUI/OpFamUI')
			if template:
				mainmenu = op('/ui/dialogs/mainmenu')
				if mainmenu:
					ui_manager = mainmenu.copy(template, name='OpFamUI')
					ui_manager.allowCooking = True
					emptypanel = mainmenu.op('emptypanel')
					if emptypanel and ui_manager.inputCOMPConnectors:
						ui_manager.inputCOMPConnectors[0].connect(emptypanel)
					if local_dev:
						ui_manager.par.enable = True
						ui_manager.par.display = True
						ui_manager.par.selectpanel = self.ownerComp.op('OpFamUI')

		return ui_manager if not local_dev else self.ownerComp.op('OpFamUI')
```

Notes on the gate:

- `mmreg.Widgets` is the MainMenuRegistry manager API (snapshot property of
  all entries). Membership of `'OpFamUI'` means some TDFam host has
  registered — which happens at the host's own extension init, typically
  BEFORE this routine runs (it is deferred to `endFrame` via `post_init`).
- **Timing edge**: on a cold boot the registry global may not exist yet when
  `post_init` fires (both sides self-install asynchronously). Worst case the
  legacy copy gets created once and is destroyed on the NEXT call into this
  routine — or never, in registry-less projects, which is the intended
  fallback. If you want zero flash-of-legacy, re-run the gate deferred:
  `run(lambda: self.get_or_create_famui_manager(), delayFrames=120,
  delayRef=op.TDResources)` at the end of `post_init`.
- `local_dev` mode is preserved untouched: the gate returns before it, so if
  you want Dev mode to bypass the registry too, move the `local_dev` read
  above the gate and add `and not local_dev` to the gate condition.

---

## 4. Behavior changes to be aware of (ship notes)

1. **The FAM button becomes manageable**: users with the FNS toolkit can
   reorder/hide it from the Main Menu Configurator like any registered
   entry; order/display persist on the host's pars (inside the OpFamUI of
   whichever TDFam copy published) and survive TD restarts via host
   republish + boot sweep.
2. **The mirror's source panel is not in `/ui`**: `OpFamUIExt` was audited —
   it has no location assumptions (resolves everything via `op.FAMREGISTRY`),
   so it runs identically from inside the registry copy. Click interaction
   goes through the mirror's panel-forwarding (same mechanism as the FNS
   projname widget). One manual click-test after porting is recommended —
   programmatic verification covered registration/render/heal but not a real
   mouse click.
3. **Upgrade path for existing user projects**: on first load of the updated
   TDFam, the host registers, the patched injector destroys the legacy
   `/ui/dialogs/mainmenu/OpFamUI`, and the mirror takes its place. No user
   action.
4. **`/sys` copy shows `Skipped (/sys or /ui)`** in its host's Regstatus —
   expected, not a failure (see §1).
5. **Registry-less projects**: `op.FNS_MAINMENUREGISTRY` missing → gate falls
   through → legacy injection exactly as today. Zero behavior change.
6. Uninstall flow: TDFam's existing uninstall only touches menu_op artifacts
   plus the legacy OpFamUI path. With the registry owning the mirror, the
   entry disappears when the last registered OpFamUI host is destroyed
   (RegistryBase `onDestroyTD` + healing prune) — i.e. removing TDFam
   removes the button without extra code.

## 5. Post-port test checklist (in a TDFam dev project)

1. Fresh project + one family comp: FAM appears right of the status area
   (right band); `/sys/MainMenuRegistry` exists; host Regstatus
   `Registered: OpFamUI -> .../OpFamUI`; no legacy
   `/ui/dialogs/mainmenu/OpFamUI` comp.
2. Click FAM → family manager opens (the manual mirror-click test).
3. Delete `mmitem_OpFamUI` by hand → reappears within ~2 s (heal tick).
4. Delete the family comp → button disappears (entry pruned) if no other
   TDFam copy is live.
5. Project with FNS toolkit installed: FAM shows in the Main Menu
   Configurator list; hide/show + reorder work and stick.
6. Project with NEITHER FNS nor the patched gate outcome: temporarily rename
   the host inside OpFamUI → legacy injection still produces the old copy
   (fallback intact).

## 6. Provenance

Prototyped live in FunctionStore_tools_2025_DEV (2026-08-12), verified:
registration from both the root master and the nested template, mirror
render at 45x19 next to the Configurator gear (screenshot-verified),
heal-after-destroy, benign dual-host last-writer-wins. Nothing was saved
into the TDFam toxes in that session — the live prototype reverts on TD
restart; this document + the exported host tox are the full port.
