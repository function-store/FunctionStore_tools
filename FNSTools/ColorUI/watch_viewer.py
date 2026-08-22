"""Watches ColorUI's own panel: winopen = the viewer is open as a floating
window. The local Web Render runs only then (and only while the console is
not serving the page) -- ExtColorUI.SyncLocalBrowser owns the rule."""


def onValueChange(panelValue, prev):
	parent.ColorUI.ext.ExtColorUI.SyncLocalBrowser()
	return
