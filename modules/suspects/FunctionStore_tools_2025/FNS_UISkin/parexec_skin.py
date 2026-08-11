# Re-applies the skin whenever one of FNS_UISkin's own parameters changes.
# Watches the whole component: every customization page this tool grows is
# covered without touching this DAT.


def onValueChange(par, prev):
	par.owner.Apply()
	return


def onPulse(par):
	par.owner.Apply()
	return
