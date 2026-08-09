# me - this DAT
# scriptOp - the OP which is cooking
#
# Node-table augmentation for TD's Insert Operator dialog, driven entirely by
# OpMenuRegistry: extra fuzzy search words and row-label decorations come from
# whatever tools have registered, so this script names no tool.
#
# press 'Setup Parameters' in the OP to call this function to re-create the parameters.
def onSetupParameters(scriptOp):
	page = scriptOp.appendCustomPage('Operators')
	p = page.appendInt('Rows', label='Rows')
	p = page.appendToggle('Append', label='Append Nodes')
	p = page.appendStr('Compatible', label='Compatible OPs')
	p = page.appendStr('Search',label='Search String')
	p = page.appendStr('Source',label='Source')
	p = page.appendStr('Connectto',label='Connect To')
	p = page.appendToggle('All',label='Display All')
	p = page.appendToggle('Experimental',label='Display Experimental')
	p = page.appendStr('Limitcustom', label='Limit Custom')
	return

# called whenever custom pulse parameter is pushed
def onPulse(par):
	return

import re
import td as TD

def onCook(scriptOp):
	registry = getattr(op, 'OPMENUREGISTRY', None)
	# Resolved once per cook -- this loop runs over every operator type.
	searchWordsDict = {}
	decorators = []
	if registry is not None:
		try:
			searchWordsDict = registry.SearchWords
			decorators = registry.Decorators
		except Exception as e:
			debug('OpMenuRegistry contributions unavailable:', e)

	scriptOp.clear()
	intab = scriptOp.inputs[0]
	scriptOp.appendRow(intab.row(0))

	## #########################
	searchString = scriptOp.par.Search.eval().lower().strip()

	#########################
	head_dict = {_head.val: _head.col for _head in intab.row(0)}
	for _row in intab.rows()[1:]:
		label = _row[head_dict['label']].val
		_name = _row[head_dict['name']].val
		if not _name:
			scriptOp.appendRow(_row)
			continue
		new_label = None
		optype = _row[head_dict['opType']].val
		score_orig = _row[head_dict['score']].val
		_type = _row[head_dict['type']].val
		family = _row[head_dict['family']].val
		try:
			score = float(str(score_orig).strip()) if score_orig != '' else 0
		except:
			score = 0
		new_score = score

		if family in families:
			# currently ignoring T3D for my opmenu mods
			_op = getattr(TD, optype, None)
			if _op is None:
				continue

		# --- registered row decorations (e.g. 'this type has a template') ---
			_lbl = label
			for _canonical, _decorate in decorators:
				try:
					_res = _decorate(optype, _lbl)
				except Exception as e:
					debug('OpMenuRegistry decorator %r failed:' % _canonical, e)
					continue
				if _res:
					_lbl = str(_res)
			if _lbl != label:
				new_label = _lbl
		# ---
			if _op and score is not None and score <= 3:
				if len(searchString) > 0:
					labelWords = label.lower().split(' ')
					labelWords.append(optype)  # add the type to the labelWords
					searchWords = searchString.lower().split(' ')

					if all(label_word.startswith(search_word) for label_word, search_word in zip(labelWords, searchWords)):
						new_score = 3
					elif len(searchWords) == 1 and score <= 2:
						extraSearchWords = searchWordsDict.get(optype, [])
						search_word = searchWords[0]
						if search_word:
							if any(re.match(search_word, extra_label) for extra_label in extraSearchWords):
								new_score = 2

					if new_score > 0:
						opType = ['defGenerator','defFilter'][_op.isFilter]
					else:
						opType = ['defGeneratorDisable','defFilterDisable'][_op.isFilter]

					_type = 'layouts/{0}/{1}'.format(family,opType)

		_row[head_dict['label']] = new_label or label
		_row[head_dict['type']] = _type
		_row[head_dict['score']] = new_score or score_orig
		scriptOp.appendRow(_row)

	return
