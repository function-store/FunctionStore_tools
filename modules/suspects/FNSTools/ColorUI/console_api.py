"""ColorUI's FNS_Console tab API -- answers /t/ColorUI/api/<action>.

The tab is ColorUI's own webui.html served by the console; over HTTP the
page POSTs its commands here (same vocabulary as the title bridge) and
polls `state`. All the work is in ExtColorUI (ConsoleState / ConsoleCommand);
this DAT only names the actions.
"""


def onConsoleRequest(action, method, body):
	ext = parent.ColorUI.ext.ExtColorUI
	if action == 'state':
		return ext.ConsoleState()
	if action == 'cmd' and method == 'POST':
		return ext.ConsoleCommand(body)
	return {'ok': False, 'why': 'unknown action: %s %s' % (method, action)}
