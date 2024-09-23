import re

class ExtOpenExt:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

	def OnOpen(self):
		_op = ui.panes.current.owner.currentChild
		if not _op.isCOMP:
			return
		
		_object = None
		for _block in _op.seq.ext:
			if _block.par.promote:
				_object = _block.par.object
				break
		if _object:
			_op_relative_path = self._getExtOpPath(_object.eval())
			if not _op_relative_path:
				return
			
			_dat = _op.op(_op_relative_path) 
			if _dat:
				_dat.par.edit.pulse()

	def _getExtOpPath(self, _object):
		pattern = r"op\('(.*?)'\)\.module\..*\(me\)"
		match = re.search(pattern, _object)
		if not match:
			return None
		return match.group(1)
		
		