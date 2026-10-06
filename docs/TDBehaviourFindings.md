---
status: in-force
summary: TouchDesigner behaviours this project measured and paid for, rescued out of .claude/rules/ so a regeneration cannot take them.
since: 2026-09-23
---

# Measured TouchDesigner behaviours

Seven findings that were discovered here, at cost, and lived only in
`.claude/rules/td-python.md`. That file is an Embody/Envoy deployment
artifact: regenerated per machine and per version, gitignored, and already
once behind by a month. Anything whose only home is a generated file is one
deploy away from gone. This is their home; the rules file may restate them.

None of these are in Derivative's documentation as stated. Each is written
with what was actually measured, so a future reader can re-run it rather
than trust it.

## 1. `findChildren(depth=N)` matches EXACTLY depth N

Use `maxDepth=N` to limit, or pass neither for unlimited. `depth=99` returns
an **empty list**, not "everything": it asks for ops exactly 99 levels down.

Measured on one COMP:

| Call | Result |
|---|---|
| `depth=1 / 2 / 3` | 8 / 225 / 705 |
| `maxDepth=1 / 2 / 3` | 8 / 233 / 938 (running total) |
| `depth=99` | 0 |
| `maxDepth=99` | 3483 |

**Why it matters:** a project-wide sweep written with `depth=` reports zero
hits and looks like a clean result. That is how a stale prompting code path
survived three "nothing found" searches. `type=` also needs a concrete class
(`textDAT`), not a family base (`DAT`).

## 2. `numpyArray()` and `copyNumpyArray()` agree with each other

A frame read from one TOP can be written to another with no flip. OpenCV is
the odd one out: it hands back top-row-first, so cv2 frames need `[::-1]`.

**Do not settle this by capturing an image and looking at it.** `capture_top`
may itself flip when writing a file, and two possibly-flipping layers cancel
into an unreadable answer. Settle it by round-tripping real data: the same
movie decoded both ways differs by **7.75/255 as-is versus 44.32 flipped**.

## 3. `ui.messageBox` blocks the main thread until it is clicked

Never put one anywhere a script, a parameter callback, or an MCP call can
reach: it wedges TD instead of warning. For a costly user-initiated action,
arm a confirm and ask for a second press. That is non-blocking, works
headless, and cannot be triggered into a hang.

## 4. A Script TOP has no `clear()`

Script DAT and Script CHOP do, which is the trap. `scriptOp.clear()` in a
Script TOP's `onCook` raises `tdAttributeError` at runtime, not at edit
time, so it only fires on the code path that has nothing to draw.

`copyNumpyArray()` is the only way a Script TOP emits anything, so "nothing
to draw" is a **transparent array at the current resolution**. An early
`return` is not equivalent: it leaves the previous frame on screen.

## 5. An OP Execute DAT cannot warn you before a monitored op dies

`onDestroy` fires after the frame with no operator (the TD 2025 template
says it is the DAT's own destruction), and `onNumChildrenChange` on the
parent fires after the fact. Any parameter expression reading the dead op
already raises by then.

The one pre-mortem hook is an extension's `onDestroyTD` on the dying COMP:
it runs inside `destroy()` with the COMP, its children and dependent
parameters still readable (measured TD 2025.33070). It also runs on reinit,
which nothing inside the call tells apart, so confirm a frame later.

Related, and separately paid for: a promoted owner lookup inside
`onDestroyTD` hangs TD on reinit. A `py-spy dump` finds the line.

## 6. A parameter evaluates a new expression the instant you write it

Setting `par.expr = "op('x/out1')['ch']"` before that CHOP has cooked reads
the channel as `None`, and the parameter raises `TypeError: float()
argument must be a string or a real number, not 'NoneType'` -- at write
time, not later.

Force-cook the source and confirm the channel exists before binding, and
re-try a frame later for anything still missing.

## 7. `root` is not reliably bound in every exec context

Use `op('/')` when you mean the project root.

---

## Where the rest of the rules drift went

The 2026-09-23 comparison of this project's `.claude/rules/` against
Embody's current generation found drift in two directions. Embody's newer
text supersedes the older local copy for naming tiers, the operator
referencing rungs (`iop` / `ipar`), the threading ladder and the
parameter/storage/dependency split -- take those from the deploy.

The hand-added "check BOTH `get_op_errors` AND `scriptErrors(recurse=True)`"
insertions in `worktree-td-safety.md` are already safe: they are in
`CLAUDE.md` rule 9 and in the `/fns-definition-of-done` skill, both tracked.
