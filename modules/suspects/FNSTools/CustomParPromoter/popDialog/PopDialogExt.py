
'''Info Header Start
Name : PopDialogExt
Author : Dan@DAN-4090
Saveorigin : FunctionStore_tools_2025_DEV.toe
Saveversion : 2025.33070
Info Header End'''
# This file and all related intellectual property rights are
# owned by Derivative Inc. ("Derivative").  The use and modification
# of this file is governed by, and only permitted under, the terms
# of the Derivative [End-User License Agreement]
# [https://www.derivative.ca/Agreements/UsageAgreementTouchDesigner.asp]
# (the "License Agreement").  Among other terms, this file can only
# be used, and/or modified for use, with Derivative's TouchDesigner
# software, and only by employees of the organization that has licensed
# Derivative's TouchDesigner software by [accepting] the License Agreement.
# Any redistribution or sharing of this file, with or without modification,
# to or with any other person is strictly prohibited [(except as expressly
# permitted by the License Agreement)].
#
# Version: 099.2017.30440.28Sep
#
# _END_HEADER_#

from TDStoreTools import StorageManager
import TDFunctions as TDF
class PopDialogExt:

	def __init__(self, ownerComp):
		"""
		Popup dialog extension. Just call the DoPopup method to create a popup.
		Provide info in that method. This component can be used over and over,
		no need for a different component for each dialog, unless you want to
		change the insides.
		"""
		self.ownerComp = ownerComp
		self.windowComp = ownerComp.op('popDialogWindow')
		self.details = None
		self.entries = self.ownerComp.ops('entry*')
		self.checkBoxes = self.ownerComp.ops('entry*/buttonCheckbox')
		for entry in self.entries:
			entry_index = tdu.digits(entry.name)
			TDF.createProperty(self, f'EnteredText{entry_index}', value='')
		for idx, checkBox in enumerate(self.checkBoxes):
			TDF.createProperty(self, f'CheckBox{idx+1}', value=False)

		
		# NOTE: an "upgrade version" block used to live here, writing
		# par.Version and rewriting the h par's expression ON EVERY INIT.
		# Mutating a CLONE's pars from __init__ is a standing war with clone
		# sync against the /sys/TDTox/popDialog master: each resync round
		# re-initializes this extension, which wipes self.details and the
		# EnteredText deps -- the dialog then opens blank and OK does nothing
		# (details=None skips both promote branches). Init must not write to
		# the comp.

		TDF.createProperty(self, 'TextHeight', value=0)
		run("args[0].UpdateTextHeight()", self, delayFrames=1, 
					delayRef=op.TDResources)

	def OpenDefault(self, text='', title='', buttons=('OK',), callback=None,
					details=None, textEntry1=False, textEntry2=False, textEntries=None, escButton=1,
					escOnClickAway=True, enterButton=1):
		self.Open(text, title, buttons, callback, details, textEntry1, textEntry2, textEntries, escButton,
				  escOnClickAway, enterButton)

	def Open(self, text=None, title=None, buttons=None, callback=None,
			 			details=None, textEntry1=None, textEntry2=None, textEntries=None, escButton=None,
			 			escOnClickAway=None, enterButton=None):
		"""
		Open a popup dialog.
		text goes in the center of the dialog. Default None, use pars.
		title goes on top of the dialog. Blank means no title bar. Default None,
			use pars
		buttons is a list of strings. The number of buttons is equal to the
			number of buttons, up to 4. Default is ['OK']
		callback: a method that will be called when a selection is made, see the
		 	SetCallback method. This is in addition to all internal callbacks.
		 	If not provided, Callback DAT will be searched.
		details: will be passed to callback in addition to item chosen.
			Default is None.
		If textEntry is a string, display textEntry field and use the string
			as a default. If textEntry is False, no entry field. Default is
			None, use pars
		escButton is a number from 1-4 indicating which button is simulated when
			esc is pressed or False for no button simulation. Default is None,
			use pars. First button is 1 not 0!!!
		enterButton is a number from 1-4 indicating which button is simulated
			when enter is pressed or False for no button simulation. Default is
			None, use pars. First button is 1 not 0!!!
		escOnClickAway is a boolean indicating whether esc is simulated when user
			clicks somewhere besides the dialog. Default is None, use pars
		"""
		self.Close()
		# text and title
		if text is not None:
			self.ownerComp.par.Text = text
		if title is not None:
			self.ownerComp.par.Title = title
		# buttons
		if buttons is not None:
			if not isinstance(buttons, list):
				buttons = ['OK']
			self.ownerComp.par.Buttons = len(buttons)
			for i, label in enumerate(buttons[:4]):
				getattr(self.ownerComp.par,
										'Buttonlabel' + str(i + 1)).val = label
		# callbacks
		if callback:
			ext.CallbacksExt.SetAssignedCallback('onSelect', callback)
		else:
			ext.CallbacksExt.SetAssignedCallback('onSelect', None)
		# textEntry
		if textEntry1 is not None:
			if isinstance(textEntry1, str):
				self.ownerComp.par.Textentryarea = True
				self.ownerComp.par.Textentrydefault = str(textEntry1)
			elif textEntry1:
				self.ownerComp.par.Textentryarea = True
				self.ownerComp.par.Textentrydefault = ''
			else:
				self.ownerComp.par.Textentryarea = False
		if textEntry2 is not None:
			if isinstance(textEntry2, str):
				self.ownerComp.par.Textentryarea2 = True
				self.ownerComp.par.Textentrydefault2 = str(textEntry2)
			elif textEntry2:
				self.ownerComp.par.Textentryarea2 = True
				self.ownerComp.par.Textentrydefault2 = ''
		
		# self.EnteredText1 = self.ownerComp.par.Textentrydefault.eval()
		# self.EnteredText2 = self.ownerComp.par.Textentrydefault2.eval()
		# keep the requested defaults for the post-open re-assert (see
		# _applyPendingEntryTexts) -- the window's field widgets wipe them
		self._pending_entry_texts = list(textEntries or [])
		for idx, (entry, text) in enumerate(zip(self.entries, textEntries or [])):
			if text is not None:
				setattr(self, f'EnteredText{idx + 1}', text)

		# set focus to first entry0
		
		run('op("' + self.entries[0].path + '").op("inputText").setKeyboardFocus(selectAll=True)',
			delayFrames=3, delayRef=op.TDResources)
		# if app.osName == 'Windows':
		self.entries[0].op('inputText').setKeyboardFocus(selectAll=True)

		for checkBox_index, checkbox in enumerate(self.checkBoxes):
			if checkbox.par.Value0.eval():
				setattr(self, f'CheckBox{checkBox_index}', False)
				
		self.details = details
		for idx, entry in enumerate(self.entries):
			entry.op('inputText').par.text = getattr(self, f'EnteredText{idx + 1}')
			entry.op('inputText').cook(force=True)
		for idx, checkBox in enumerate(self.checkBoxes):
			checkBox.par.Value0.val = getattr(self, f'CheckBox{idx}')

		if escButton is not None:
			if escButton is False or not (1 <= escButton <= 4):
				self.ownerComp.par.Escbutton = 'None'
			else:
				self.ownerComp.par.Escbutton = str(escButton)
		if escOnClickAway is not None:
			self.ownerComp.par.Esconclickaway = escOnClickAway
		if enterButton is not None:
			if enterButton is False or not (1 <= enterButton <= 4):
				self.ownerComp.par.Enterbutton = 'None'
			else:
				self.ownerComp.par.Enterbutton = str(enterButton)
		self.UpdateTextHeight()
		# NOTE: a replicator recreateall pulse used to live here ("HACK
		# shouldn't be necessary"). It recreated the five entry COMPs on
		# EVERY open: the freshly-set defaults were wiped as the new
		# replicants initialized their bound text pars, and the entry
		# references cached in __init__ went stale -- blank dialog, dead OK.
		self.actualOpen()
		# run("op('" + self.ownerComp.path + "').ext.PopDialogExt.actualOpen()",
		# 								delayFrames=1, delayRef=op.TDResources)

	def actualOpen(self):
		# needs to be deferred so that sizes can update properly
		self.windowComp.par.winopen.pulse()
		# The field widgets initialize as the window opens and push their
		# (empty) panel text through the text-par BINDs into the EnteredText
		# dependencies -- wiping the defaults Open() just set. Re-assert them
		# once the fields have settled. (Measured: the wipe lands within the
		# first frames after winopen.)
		run("args[0]._applyPendingEntryTexts()", self,
			delayFrames=5, delayRef=op.TDResources)
		# second pass: the min/max/default fields become visible only when
		# Minmaxentryarea flips, so they initialize (and wipe) later than
		# the name/label fields
		run("args[0]._applyPendingEntryTexts()", self,
			delayFrames=20, delayRef=op.TDResources)
		ext.CallbacksExt.DoCallback('onOpen')
		if self.ownerComp.op('entry1').par.display.eval():
			self.ownerComp.setFocus()
			# self.ownerComp.op('entry1/inputText').setKeyboardFocus(selectAll=True)
			# hack shouldn't have to wait a frame
			run('op("' + self.ownerComp.path + '").op("entry1/inputText").'
			 				'setKeyboardFocus(selectAll=True)',
			 				delayFrames=1, delayRef=op.TDResources)
			if app.osName == 'Windows':
				self.ownerComp.op('entry1/inputText').setKeyboardFocus(selectAll=True)
		else:
			self.ownerComp.setFocus()

	def _applyPendingEntryTexts(self):
		"""Re-apply the defaults requested by the last Open() after the
		window's field widgets have initialized (they wipe the bound
		EnteredText deps with their empty panel state on open)."""
		texts = getattr(self, '_pending_entry_texts', None) or []
		for idx, (entry, text) in enumerate(zip(self.entries, texts)):
			if text is None or not entry.valid:
				continue
			setattr(self, f'EnteredText{idx + 1}', text)
			entry.op('inputText').par.text = getattr(self, f'EnteredText{idx + 1}')

	def Close(self):
		"""
		Close the dialog
		"""
		#ext.CallbacksExt.SetAssignedCallback('onSelect', None)
		ext.CallbacksExt.DoCallback('onClose')
		self.windowComp.par.winclose.pulse()
		for idx, entry in enumerate(self.entries):
			# .eval() is load-bearing: storing the Par OBJECT puts it in the
			# dependency these pars BIND to -- evaluating the par then evaluates
			# the master which returns the par itself = recursion/loop error,
			# and the whole dialog reads blank from then on.
			setattr(self, f'EnteredText{idx + 1}', entry.op('inputText').par.text.eval())
		for idx, checkBox in enumerate(self.checkBoxes):
			setattr(self, f'CheckBox{idx}', checkBox.par.Value0.eval())

	def OnButtonClicked(self, buttonNum):
		"""
		Callback from buttons
		"""
		infoDict = {'buttonNum': buttonNum,
					'button': getattr(self.ownerComp.par,
										'Buttonlabel' + str(buttonNum)).eval(),
					'details': self.details}
		if self.ownerComp.par.Textentryarea.eval():
			infoDict['enteredText'] = []
			infoDict['checkBoxes'] = []
			for entry in self.entries:
				infoDict['enteredText'].append(entry.op('inputText').par.text.eval())
			for checkBox in self.checkBoxes:
				infoDict['checkBoxes'].append(checkBox.par.Value0.eval())
			
		try:
			ext.CallbacksExt.DoCallback('onSelect', infoDict)
		finally:
			self.Close()
		
	def OnKeyPressed(self, key):
		"""
		Callback for esc or enterpressed.
		"""
		if key == 'esc' and self.ownerComp.par.Escbutton.eval() != 'None':
			button = int(self.ownerComp.par.Escbutton.eval())
			if button <= self.ownerComp.par.Buttons:
				self.OnButtonClicked(button)
		elif key == 'enter' and self.ownerComp.par.Enterbutton.eval() != 'None':
			button = int(self.ownerComp.par.Enterbutton.eval())
			if button <= self.ownerComp.par.Buttons:
				self.OnButtonClicked(button)
		elif key == 'tab' and not self.ownerComp.op('KeyModifiers1/out1')['shift'].eval():
			# get currently focused entry and move to next entry
			currIdx = None
			for idx, entry in enumerate(self.entries):
				if entry.op('inputText').panel.focusselect:
					currIdx = idx
					break
			if currIdx is not None:
				newEntry = self.entries[(currIdx + 1) % len(self.entries)]
				run('op("' + newEntry.path + '").op("inputText").setKeyboardFocus(selectAll=True)',
					delayFrames=1, delayRef=op.TDResources)
				if app.osName == 'Windows':
					newEntry.op('inputText').setKeyboardFocus(selectAll=True)
		elif key == 'shift.tab':
			# get currently focused entry and move to previous entry
			currIdx = None
			for idx, entry in enumerate(self.entries):
				if entry.op('inputText').panel.focusselect:
					currIdx = idx
					break
			if currIdx is not None:
				newEntry = self.entries[(currIdx - 1) % len(self.entries)]
				run('op("' + newEntry.path + '").op("inputText").setKeyboardFocus(selectAll=True)',
					delayFrames=1, delayRef=op.TDResources)
				if app.osName == 'Windows':
					newEntry.op('inputText').setKeyboardFocus(selectAll=True)


	def OnClickAway(self):
		"""
		Callback for esc pressed. Only happens when Escbutton is not None
		"""
		if self.ownerComp.par.Esconclickaway.eval():
			self.OnKeyPressed('esc')

	def OnParValueChange(self, par, val, prev):
		"""
		Callback for when parameters change
		"""
		if par.name == "Textentryarea":
			self.ownerComp.par.Textentrydefault.enable = par.eval()
		if par.name == "Escbutton":
			self.ownerComp.par.Esconclickaway.enable = par.eval() != "None"

	def OnParPulse(self, par):
		if par.name == "Open":
			self.Open()
		elif par.name == "Close":
			self.Close()
		elif par.name == 'Editcallbacks':
			dat = self.ownerComp.par.Callbackdat.eval()
			if dat:
				dat.par.edit.pulse()
			else:
				print("No callback dat for", self.ownerComp.path)
		elif par.name == 'Helppage':
			ui.viewFile('https://docs.derivative.ca/'
						'index.php?title=Palette:popDialog')

	def UpdateTextHeight(self):
		self.TextHeight = self.ownerComp.op('text/text').evalTextSize(
													self.ownerComp.par.Text)[1]

	@property
	def DialogHeight(self):
		return 65 + self.TextHeight*0 + \
				(20 if self.ownerComp.par.Title else 0) + \
				(37 if self.ownerComp.par.Textentryarea else 0) * len([entry for entry in self.entries if entry.par.display.eval()]) - 20