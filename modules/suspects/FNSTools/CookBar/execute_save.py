# Written for FNSTools. A project saved while the bar is on would keep the
# bar's changes to the network you are viewing (display flags off,
# annotations dimmed). Put them back for the save and draw again right after.

def onProjectPreSave():
	ext = getattr(parent().ext, 'CookBarExt', None)
	if ext is not None:
		ext.beforeSave()
	return

def onProjectPostSave():
	ext = getattr(parent().ext, 'CookBarExt', None)
	if ext is not None:
		ext.afterSave()
	return
