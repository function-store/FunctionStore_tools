# me - this DAT.
# 
# dat - the changed DAT
# prevDAT - the DAT containing previous contents.
#
# Info contains specific details on what's changed:
#
#	rowsChanged	- list of row indices with different contents
#   rowsAdded		- list of added row name indices (in dat)
#   rowsRemoved	- list of removed row name indices (in prevDAT)
#
#	colsChanged	- list of column indices with different contents
#   colsAdded		- list of added column name indices (in dat)
#   colsRemoved	- list of removed column name indices (in prevDAT)
#
#	cellsChanged 	- list of cells that have changed content
#
#	sizeChanged	- bool, true if number of rows or columns changed
# 
# Make sure the corresponding toggle is enabled in the DAT Execute DAT.
# 

# This callback can be used to evaluate several change conditions simultaneously.

def onTableChange(dat, prevDAT, info):
	text = dat.text
	text = text.replace('=============','')
	text = text.replace('==========','')
	text = text.replace('Compute Shader Compile Results:','')
	parent.ExpressionPOP.par.Info = text
	return


# These legacy callbacks can be used to track individual changes.
# Note that if rows or columns are deleted, sizeChange will be called instead
# of row/col/cellChange.

# rows - a list of row indices
def onRowChange(dat, rows):
	return

# cols - a list of column indices
def onColChange(dat, cols):
	return

# cells - list of cells that have changed content
# prev - list of previous string contents of the changed cells
def onCellChange(dat, cells, prev):
	return

def onSizeChange(dat):
	return
	