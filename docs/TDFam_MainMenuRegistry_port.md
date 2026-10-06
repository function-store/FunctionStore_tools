---
status: in-force
summary: 'Manual port guide handed to the TDFam repo: replacing its fire-and-forget mainmenu copy with a MainMenuRegistry-managed entry. External deliverable.'
since: 4022dc4 2026-08-13
---

# TDFam x MainMenuRegistry -- manual port guide

Port of the live prototype (verified 2026-08-12 in FunctionStore_tools_2025_DEV)
that replaces TDFam's fire-and-forget `OpFamUI` copy in `/ui/dialogs/mainmenu`
with a **MainMenuRegistry-managed entry**: ordered/showable from the FNS
Main Menu Configurator, healed by the registry watch tick, and fully
backwards-compatible with projects that have no FNS tools installed.

Two deliverables sit next to this file:

- **`TDFam_MainMenuRegistry_host.tox`** -- the configured host component,
  exported portable (no external file references, no clone binding, no
  Embody metadata). This is the only new component TDFam ships.
- This document -- one component drop, one small callbacks DAT (text in
  section 3), and one function patch.

---

## 1. What goes where (summary)

| # | Change | Where in the TDFam repo |
|---|---|---|
| 1 | Drop `TDFam_MainMenuRegistry_host.tox` as a child named **`FNS_MainMenuRegistry`** INSIDE the **`OpFamUI`** component (the name must equal the registry's `REGISTRY_NAME` -- the global's boot sweep finds unpublished hosts by that exact name) | the TDFamRegistry master (wherever `TDFamRegistry/OpFamUI` is authored -- it propagates into the nested template in `TDFam_create` and into every shipped copy from there) |
| 2 | Patch **`get_or_create_famui_manager`** in `GlobalUIInjector` (the gate + slot-holder), and call it at the end of `install()` / `uninstall()` | the GlobalUIInjector DAT/module of TDFamRegistry |
| 3 | Add a **`mainmenu_callbacks`** text DAT beside the host INSIDE `OpFamUI` (the host's `Create Callbacks` pulse makes it; its `onRegistered` re-runs the gate) | same place as the host |
| 4 | (nothing else -- no other TDFam code touches the mainmenu path) | |

Design shape (matches the FNS registry scheme's "host lives INSIDE the
component it registers"): the host sits in `OpFamUI` with `Comp = ..`, so it
registers the very panel it lives in. It is present in every TDFamRegistry
copy. `TDFam_create` is the bootstrapper: each family comp carries a nested
TDFamRegistry template in the user's network and promotes a copy to
`/sys/TDFamRegistry` (`op.FAMREGISTRY`). The promoted `/sys` copy's host is
automatically neutralized by the scheme's `/sys`-guard (its `Regstatus`
reads `Skipped (/sys or /ui)`) -- that is correct and expected. Registration
always comes from the network-side copies (the nested template inside each
family comp, and the dev master), which is exactly the redundancy you want:
any one live copy keeps the FAM button alive; healing re-registers from a
survivor if the current publisher dies.

---

## 2. The host component (deliverable 1)

`TDFam_MainMenuRegistry_host.tox` is a copy of the FNS `FNS_MainMenuRegistry`
(v0.2.1, `RegistryBase`-based, exported 2026-08-23) already configured for
TDFam. Do NOT use the 2026-08-12 export of the same name: it predates the
registry rename (`MAINMENUREGISTRY` -> `FNS_MAINMENUREGISTRY`, 2026-08-15) and
the move of the globals into `/sys/FNS_Registries` (2026-08-21), so in a
project with current FNS tools it would install a second, differently-named
global whose heal tick fights the real one over the bar's mirrors. If you
prefer to configure a fresh copy from the FNS_MainMenu package instead, these
are the exact values (Registration page, everything else at defaults):

| Par | Value | Why |
|---|---|---|
| `Comp` | `..` (constant, the default) | registers the OpFamUI panel the host lives inside |
| `Canonicalname` | `OpFamUI` | the entry name in the global registry (and the mirror name: `mmitem_OpFamUI`) |
| `Callback` | `mainmenu_callbacks` (bare sibling name) | the DAT in section 3; its `onRegistered` closes the cold-boot race. Pulse the host's `Create Callbacks` to create it and set this par in one go |
| `Autoregister` | **On** | publishes whenever this copy initializes outside `/sys` |
| `Menuorder` | `-1` | default append within the side band |
| `Align` | **`right`** | places the mirror in the right band -- between the stretchy status area and the right corner, i.e. next to the Configurator gear, where the legacy copy sat |
| `Anchor` | empty | side band is sufficient; no pin to a named stock item |
| `Displayed` | On | |
| `Barwidth` | `0` | mirror width live-follows the source panel (45 px) |
| `Helpurl` | empty (or your wiki page -- shows on right-click in the Configurator) | |
| `Promotepars` | **Off** | deliberate: don't grow a bound `Registry` page on the OpFamUI panel comp |
| `clone` | **empty**, `enablecloning` Off | ship clean. In projects that carry the FNS MainMenu package, the FNS global's healing tick re-binds the clone automatically (`_healHostClones`, to `op.FNS.op('FNS_MainMenuRegistry') if hasattr(op, 'FNS') else None`); everywhere else the host is standalone and updated by TDFam's own updater |
| COMP `externaltox` | empty, `enableexternaltox` Off | **critical** -- an inherited externaltox on a copied host reloads the WRONG tox into it at boot (hazard paid for during the FNS port) |
| tags | `FNS_MainMenuRegistry` only | findability convention; do NOT let it inherit `pi_suspect` or any tracker tag from your pipeline |

Also embedded in the tox: `MainMenuRegistryExt`, `RegistryBase`,
`callbacks_template`, `pre_release`, `ExtUtils` -- all with file bindings
stripped (text embedded), so nothing dangles in the TDFam repo. Leave them
that way; do NOT re-bind `RegistryBase` to a file unless you adopt the FNS
shared-file workflow.

**Placement inside OpFamUI**: anywhere clear in the network (the prototype
put it below the existing children's bounding box). It has no wires.

**What the host does on init** (so you know what "working" looks like):
outside `/sys` it installs/updates the `/sys/FNS_Registries/FNS_MainMenuRegistry`
global (reached as `op.FNS_MAINMENUREGISTRY` -- always by shortcut, never by
path) if the FNS package isn't already providing one (the host IS the
bootstrap -- TDFam works in a bare project with zero FNS tools), then
registers `OpFamUI`.
The global then builds `mmitem_OpFamUI` (a selectCOMP mirror of the panel,
height-enforced to the bar's 19 px, width following the source) wired to the
bar's `emptypanel`, and heals it every ~2 s watch tick. Two or more TDFam
copies registering the same canonical is benign -- the entries are
equivalent, last writer wins, healing keeps one mirror.

---

## 3. The code patch (deliverable 2)

`GlobalUIInjector.get_or_create_famui_manager` currently copies the OpFamUI
template into `/ui/dialogs/mainmenu` unconditionally. Gate it on the
registry entry so the two mechanisms can never double-inject, prune the
legacy copy when the registry takes over, and **hold the legacy slot** with
an inert marker so that an OLDER TDFam family dropped into the project later
(its own, unpatched injector runs at its init, before version reconciliation)
finds `/ui/dialogs/mainmenu/OpFamUI` already present and stands down -- that
existence check is the one contract every shipped injector honours. The
marker is a bare `baseCOMP`: not a panel, so it renders nothing and stays out
of the bar's layout flow and the registry's stock-item scan. Replacement for
the whole function (current body: the
`ui_manager_path = '/ui/dialogs/mainmenu/OpFamUI'` version; only the marked
block is new):

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
		mmreg = getattr(op, 'FNS_MAINMENUREGISTRY', None)
		if mmreg and mmreg.valid and mmreg.extensionsReady:
			try:
				mainmenu = op('/ui/dialogs/mainmenu')
				if 'OpFamUI' in mmreg.Widgets:   # registered -> registry owns the bar
					if ui_manager and ui_manager.OPType != 'baseCOMP':
						ui_manager.destroy()     # retire a real legacy copy
						ui_manager = None
					if not ui_manager and mainmenu:
						# inert slot-holder: every legacy injector checks this
						# path first and stands down when it exists, so an
						# older family dropped in later cannot re-inject
						marker = mainmenu.create(baseCOMP, 'OpFamUI')
						marker.comment = 'FAM button is MainMenuRegistry-managed: see mmitem_OpFamUI'
						marker.nodeX = 500
						marker.nodeY = -900
					return None
				if ui_manager and ui_manager.OPType == 'baseCOMP':
					ui_manager.destroy()         # registry gave the bar back
					ui_manager = None
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

Also call the gate at the end of the `try:` block of both `install()` and
`uninstall()` in the same class -- every family, old or new, installs through
the GLOBAL registry, so this re-evaluates bar ownership whenever a family
comes or goes:

```python
			self._setup_keyboard_nav()

			# registry takeover: prune a legacy OpFamUI copy an older
			# family's injector may have dropped into the bar
			self.get_or_create_famui_manager()
```

```python
				# If families remain, just update the script
				self._setup_last_node_type()

			# registry takeover: re-evaluate who owns the FAM button
			self.get_or_create_famui_manager()
```

And the callbacks DAT (`OpFamUI/mainmenu_callbacks`, referenced by the host's
`Callback` par). The registry calls `onRegistered` synchronously inside
`RegisterWidget`, on EVERY publish (first registration, boot re-application,
healing re-publish) -- i.e. exactly when `'OpFamUI' in Widgets` becomes true.
`me` is the DAT, so the walk up is relative and correct in every copy:

```python
def onRegistered(canonical, info):
	"""Our entry is live in the global registry. Re-run the injector gate
	NOW: it retires a legacy /ui/dialogs/mainmenu/OpFamUI copy injected
	while the registry was not ready yet (cold-boot race) and places the
	inert slot-holder that keeps older family injectors from re-injecting."""
	reg = me.parent().parent()          # OpFamUI -> this TDFamRegistry copy
	ext = getattr(reg.ext, 'OpFamRegistryExt', None) if reg is not None and reg.extensionsReady else None
	inj = getattr(ext, 'global_ui_injector', None)
	if inj is not None:
		inj.get_or_create_famui_manager()
	return


def onUnregistered(canonical):
	return


def onDisplayChanged(canonical, visible):
	return


def onSideChanged(canonical, side):
	return
```

Notes on the gate:

- `mmreg.Widgets` is the MainMenuRegistry manager API (snapshot property of
  all entries). Membership of `'OpFamUI'` means some TDFam host has
  registered -- which happens at the host's own extension init, usually
  BEFORE this routine runs (it is deferred to `endFrame` via `post_init`).
- **Cold-boot race, closed by `onRegistered`**: `/sys` is never saved, so on
  every boot the MainMenuRegistry global, the host and its entry are rebuilt
  at runtime -- in the same first frames as TDFamRegistry's own extension
  init. If `post_init` fires before the entry has landed, the gate falls
  through and the NEW injector itself copies the legacy container into the
  bar; a few frames later the mirror appears and you have two buttons, and
  nothing would call this routine again before the next restart. The
  `onRegistered` hook runs the gate at the exact moment the entry lands, so
  that container is retired and the marker placed -- no delay constant, no
  polling. (The old suggestion of a blind `delayFrames=120` re-run is
  superseded.)
- **Mixed versions, both orders**: OLD families present, NEW one dropped in
  -> the new registry wins `/sys` (newer version replaces), the host
  registers, the gate retires the legacy container. NEW present, OLD family
  dropped in -> the old copy's unpatched injector runs at its init and finds
  the marker, so it stands down; its version reconciliation then leaves it
  inert. Without the marker this second order yields two buttons, because
  the old injector runs BEFORE the old copy learns it lost.
- `famui_manager` (the return value) is stored by `post_init` and read by
  nothing, so returning `None` -- or, for old injectors, adopting the marker
  as "already installed" -- is safe.
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
2. **The mirror's source panel is not in `/ui`**: `OpFamUIExt` was audited --
   it has no location assumptions (resolves everything via `op.FAMREGISTRY`),
   so it runs identically from inside the registry copy. Click interaction
   goes through the mirror's panel-forwarding (same mechanism as the FNS
   projname widget). One manual click-test after porting is recommended --
   programmatic verification covered registration/render/heal but not a real
   mouse click.
3. **Upgrade path for existing user projects**: on first load of the updated
   TDFam, the host registers, the patched injector destroys the legacy
   `/ui/dialogs/mainmenu/OpFamUI`, and the mirror takes its place. No user
   action.
4. **`/sys` copy shows `Skipped (/sys or /ui)`** in its host's Regstatus --
   expected, not a failure (see section 1).
5. **Registry-less projects**: `op.FNS_MAINMENUREGISTRY` missing -> gate falls
   through -> legacy injection exactly as today. Zero behavior change.
6. Uninstall flow: TDFam's existing `GlobalUIInjector.uninstall` only touches
   menu_op artifacts -- it never removed the legacy `/ui/dialogs/mainmenu/OpFamUI`
   copy either. With the registry owning the mirror, the entry disappears when
   the last registered OpFamUI host is destroyed (RegistryBase `onDestroyTD` +
   healing prune) -- i.e. removing TDFam removes the button without extra code.
7. **The marker**: while the registry owns the bar, `/ui/dialogs/mainmenu/OpFamUI`
   exists as an inert `baseCOMP` (comment says why). It is not the button --
   `mmitem_OpFamUI` is. It lives in `/ui`, so it is rebuilt every session by
   the gate; if the registry ever stops carrying the entry, the gate removes
   it and the legacy path takes over again.

## 5. Post-port test checklist (in a TDFam dev project)

1. Fresh project + one family comp: FAM appears right of the status area
   (right band); `op.FNS_MAINMENUREGISTRY` resolves (to
   `/sys/FNS_Registries/FNS_MainMenuRegistry`); host Regstatus
   `Registered: OpFamUI -> .../OpFamUI`; no legacy
   `/ui/dialogs/mainmenu/OpFamUI` comp.
2. Click FAM -> family manager opens (the manual mirror-click test).
3. Delete `mmitem_OpFamUI` by hand -> reappears within ~2 s (heal tick).
4. Delete the family comp -> button disappears (entry pruned) if no other
   TDFam copy is live.
5. Project with FNS toolkit installed: FAM shows in the Main Menu
   Configurator list; hide/show + reorder work and stick.
6. Project with NEITHER FNS nor the patched gate outcome: temporarily rename
   the host inside OpFamUI -> legacy injection still produces the old copy
   (fallback intact).
7. Project with the new family live: drop in an OLD-version family comp ->
   still exactly one FAM button (the mirror); `/ui/dialogs/mainmenu/OpFamUI`
   is the `baseCOMP` marker, not a container.
8. Boot-race drill: delete the marker, create a bare `containerCOMP` named
   `OpFamUI` in `/ui/dialogs/mainmenu`, pulse `Register` on the host -> the
   container is gone and the marker is back (that is `onRegistered` doing
   its job).

## 6. Provenance

Prototyped live in FunctionStore_tools_2025_DEV (2026-08-12), verified:
registration from both the root master and the nested template, mirror
render at 45x19 next to the Configurator gear (screenshot-verified),
heal-after-destroy, benign dual-host last-writer-wins. Nothing was saved
into the TDFam toxes in that session -- the live prototype reverts on TD
restart; this document + the exported host tox are the full port.

**Revision 2026-08-23.** The registry was renamed after the prototype
(`MainMenuRegistry` -> `FNS_MainMenuRegistry`, shortcut `FNS_MAINMENUREGISTRY`,
globals under `/sys/FNS_Registries`), so the 2026-08-13 text and the
2026-08-12 tox were stale. Re-audited against the live v0.2.1 registry: host
name, shortcut and global path corrected above; the gate in section 3 now reads
`op.FNS_MAINMENUREGISTRY`. The dev-master host in
`FunctionStore_tools_2025_DEV` was re-stamped through `StampHost` (the
earlier hand-made copy had an absolute `Comp` path to the hidden inner
`OpFamUI/OpFamUI` select, `Autoregister` off, and an inherited
`externaltox` + `pi_suspect` binding -- every hazard in the section 2 table at once).
The host tox was re-exported from the v0.2.1 master.

**Revision 2026-08-23 (later the same day).** Added the slot-holder marker,
the `install()`/`uninstall()` gate calls and the `mainmenu_callbacks`
`onRegistered` hook, after working through the mixed-version cases. Verified
live on `/TDFam_create/TDFamRegistry` (v1.1.0, nested template) against the
`/sys/TDFamRegistry` global: marker placed after reinit with the mirror the
only button; an unpatched injector's existence check stands down on the
marker; a planted legacy container is retired and the marker restored on the
host's republish. The host tox is unchanged by this revision (the callbacks
DAT lives in OpFamUI, beside the host, not inside it).
