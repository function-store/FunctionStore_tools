# Drag/Drop callbacks for FNS_Hub -- the hub window (panel) AND the FNS
# main-menu button (select1; its main-menu mirror forwards the drop).
# Drop any panel COMP to register it into a surface: HubExt offers every
# tab that can package a drop (the configurators) and the chosen one stamps
# its registry host into the dropped COMP. Nothing runs inside the
# drop-event stack -- RouteDrop defers by a frame.

def onHoverStartGetAccept(comp, info):
	return parent.Hub.AcceptsDrop(info.get('dragItems', []))


def onDropGetResults(comp, info):
	parent.Hub.RouteDrop(info.get('dragItems', []))
	return {}
