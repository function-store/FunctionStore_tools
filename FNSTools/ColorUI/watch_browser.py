"""Watches the webrender info DAT (webBrowser/info1) and forwards
document.title rewrites — the page->TD half of the ColorUI web bridge."""


def _forward(dat, rows):
	for i in rows:
		row = dat.row(i)
		if row and row[0].val == 'title':
			parent.ColorUI.ext.ExtColorUI.OnBrowserTitle(row[1].val)


def onRowChange(dat, rows):
	_forward(dat, rows)
	return


def onCellChange(dat, cells, prev):
	rows = {c.row for c in cells}
	_forward(dat, rows)
	return


def onTableChange(dat):
	return
