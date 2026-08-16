---
package: ClearPars
summary: Clear parameter errors on an operator by converting broken Bind/Expression parameters to Constant values, and clear its script errors.
features:
  - name: ClearPars
    anchor: clearpars
---

## ClearPars

Clears parameter errors on an operator: any parameter left in `Bind` mode with no valid bind master, or in `Expression` mode whose expression currently raises, is switched to `Constant` mode (dropping the dangling bind/expression). `COMP`s also have their script errors cleared.
   - **Recursive**: also processes the operator's immediate children (excluding annotations)
