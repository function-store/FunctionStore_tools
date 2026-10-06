---
package: ExpressionPOP
summary: 'Per-point attribute expressions for POPs: write lines like P = P + N * 0.1 and they compile to a GLSL compute shader, with local variables carried between lines. An alternative for the Math Combine POP.'
features:
  - name: What it is
    anchor: what-it-is
  - name: Inputs and outputs
    anchor: inputs-and-outputs
---

## What it is

ExpressionPOP lets you write point math the way you would say it. Each line is one expression, such as `P = P + N * 0.1` or `Color = vec4(P, 1)`, and any point attribute of the input can be read by its name. The lines compile into a GLSL compute shader that runs on the GPU, so the math stays fast however many points come in.

A line assigns either to an output attribute or to a local variable. Locals need a GLSL type, like `vec3 offset = N * 0.2`, and every later line can use them, so a long calculation can be broken into readable steps.

It is the alternative for the Math Combine POP: create a Math Combine POP with the alternatives shortcut held and ExpressionPOP is offered in its place, wired into the same spot. It is also a member of the FNS operator family: pick it from the **FNS** tab of the OP Create dialog and it lands as one node.

## Inputs and outputs

- **in1** (POP): the points to process.
- **out_pop** (POP): the points with the expressions applied.
- **out_code** (DAT): the generated shader code.
- **out_info** (DAT): the compile result.
