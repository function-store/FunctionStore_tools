import re
from extUtils import CustomParHelper

# This is a callback system for parameters. 
# to use:
#	- create a function in ParCallbacksExt/ParCallbacks
#	  using the same name as the parameter.

def onValueChange(par, prev):
	## In Extension code implement as follows:
	# def On<Insert Paramname Here>(self, _par, _val, _prev):
	# 	...
	CustomParHelper.OnValueChange(me.par.op.eval(), par, prev)

def onPulse(par):
	## In Extension code implement as follows:
	# def On<Insert Paramname Here>(self, _par):
	# 	...
	CustomParHelper.OnPulse(me.par.op.eval(), par)