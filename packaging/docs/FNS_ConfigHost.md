---
package: FNS_ConfigHost
summary: 'A standalone FNS_ConfigRegistry host: drop it into a component to give that component roaming settings.'
features:
  - name: Config Host
    anchor: config-host
  - name: Adopting it
    anchor: adopting-it
---

## Config Host

Every FNS tool that remembers its settings does so by carrying a small
**FNS_ConfigRegistry host**. This is that host on its own, so a component
outside the toolkit can have the same thing: its parameters are written into
the shared settings file and restored on load.

It needs [FNS_ConfigRegistry](/docs/fns-configregistry/) present; the host
publishes into that registry, which owns the file. Without it the host simply
stays idle.

## Adopting it

Drag the COMP inside the component whose settings should roam, then set its
**Registration** page:

| Par | Meaning |
|---|---|
| `Comp` | the component whose parameters are saved; defaults to `..` |
| `Canonicalname` | the section name in the settings file; empty = the component's name |
| `Autoregister` | publish while the component exists |
| `Autoload` | restore saved values when it registers |
| `Persistpars` | save the component's custom parameters |
| `Excludepars` / `Excludepages` | leave named parameters or whole pages out |
| `Callback` / `Createcallbacks` | optional DAT for save/load hooks; the pulse writes a starter |

`Promotepars` mirrors the key parameters onto the parent as a bound **Registry**
page, so it can be configured without opening the host.

### The one thing to get right

**`Canonicalname` is the key your settings are stored under.** Renaming it
orphans everything saved under the old name; the values remain in the
file, but the component stops seeing them. Choose it once.

Whether settings roam across all your projects or stay with one is decided by
FNS_ConfigRegistry's scope, not here.
