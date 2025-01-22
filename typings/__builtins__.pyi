from td import *
import parameter
import parameterTypes
class abletonlinkCHOP(CHOP,OP):
	""""""
	par : parameter.abletonlinkCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.abletonlinkCHOP & parameter.CHOP & parameter.OP"""
	pass


class Vector():
	"""The vector class holds a single 3 component vector. A vector describes a direction in space, and it's important to use a vector or [[Position Class|Position]] as appropriate for the data that is being calculated. When being multiplied by a [[Matrix Class|Matrix]], this class will implicitly have a 4th component (W component) of 0. A new vector can be created without any arguments, with 3 arguments for the x,y,z values, or with a single argument which is a variable that has 3 entries such as a list of length 3, or a position or vector.

Examples of creating a vector:

```python


v = tdu.Vector() # starts as (0, 0, 0)

v2 = tdu.Vector(0, 0, -1)

values = [0, 1, 0]

v3 = tdu.Vector(values)



# vectors can be accessed like Python lists

print(v3[1])	# same as v3.y

v3[2] = 1		# same as v3.z


```
"""
	x : float
	"""Gets or sets the X component of the vector."""
	y : float
	"""Gets or sets the Y component of the vector."""
	z : float
	"""Gets or sets the Z component of the vector."""
	par : parameter.Vector
	"""Parameters of parameter.Vector"""
	def angle(self, vec) -> float: 
		"""Returns the angel (in degrees) between the current vector and specified vector (vec).

```python


d = v.angle(v2)


```"""
		pass
	def scale(self, x, y, z) -> None: 
		"""Scales each component of the vector by the specified values.

* x, y, z - The values to scale each component of the vector by.

```python


v.scale(1, 2, 1)


```"""
		pass
	def normalize(self, ) -> None: 
		"""Makes the length of this vector 1.

```python


m.normalize()


```"""
		pass
	def length(self, ) -> float: 
		"""Returns the length of this vector.

```python


l = m.length()


```"""
		pass
	def lengthSquared(self, ) -> float: 
		"""Returns the squared length of this vector.

```python


l = v.lengthSquared()


```"""
		pass
	def copy(self, ) -> any: 
		"""Returns a new vector that is a copy of the vector.

```python


newV = v.copy()


```"""
		pass
	def distance(self, vec) -> float: 
		"""Returns the distance of the current vector to specified vector (vec).

```python


l = v.distance(v2)


```"""
		pass
	def lerp(self, vec2, t) -> any: 
		"""Returns the linear interpolation of this vector and vec2. That is vec1 *  (1.0 - t) + vec2 *  t, where vec1 is the current vector.  The value for t is not restricted to the range [0, 1].

```python


l = v.lerp(v2, t)


```"""
		pass
	def slerp(self, vec2, t) -> any: 
		"""Returns the spherical interpolation of this vector and vec2. The value for t is not restricted to the range [0, 1].

```python


l = v.slerp(v2, t)


```"""
		pass
	def dot(self, vec) -> float: 
		"""Returns the dot product of this vector and the passed vector.

* vec - The other vector to use to calculate the dot product

```python


d = v.dot(otherV)


```"""
		pass
	def cross(self, vec) -> any: 
		"""Returns the cross product of this vector and the passed vector. The operation is self cross vec.

* vec - The other vector to use to calculate the cross product.

```python


c = v.cross(otherV)


```"""
		pass
	def project(self, vec, vec) -> None: 
		"""Projects this vector onto the plan defined by vec1 and vec2. Both vec1 and vec2 must be normalized. The result may not be normalized.

* vec1, vec2 - The  vectors that specify the plane to project onto. Must be normalized.

```python


v.project(v1, v2)


```"""
		pass
	def reflect(self, vec) -> None: 
		"""Reflects the current vector about the specified vector (vec).

```python


v.reflect(v2)


```"""
		pass
	pass


class Undo():
	"""A class to enable and disable undo functionality. Undo blocks can be created during python callbacks. At the end of callbacks, any dangling undo blocks will be terminated."""
	globalState : bool
	"""Is global undo enabled or not."""
	redoStack : list
	"""A list of names for redo operations available."""
	state : bool
	"""Is undo enabled or not."""
	undoStack : list
	"""A list of names for undo operations available."""
	par : parameter.Undo
	"""Parameters of parameter.Undo"""
	def startBlock(self, name, enable=True) -> None: 
		"""Start a named undo block."""
		pass
	def clear(self, ) -> None: 
		"""Clear undo and redo stack. This will terminate any current undo blocks."""
		pass
	def addCallback(self, callback, info=None) -> None: 
		"""Add a Python callback into the undo block

*  callback - user defined callback in the form of <syntaxhighlight lang=python inline>callback(isUndo, info)</syntaxhighlight>

*  info - this argument will be passed back to user in the callback"""
		pass
	def redo(self, ) -> None: 
		"""Redo the next operation. This will terminate any current undo blocks."""
		pass
	def undo(self, ) -> None: 
		"""Undo the last operation. This will terminate any current undo blocks."""
		pass
	def endBlock(self, ) -> None: 
		"""Terminate an undo block."""
		pass
	pass


class Textport():
	"""This class defines the interface to a texport interface.."""
	par : parameter.Textport
	"""Parameters of parameter.Textport"""
	pass


class TextLine():
	"""A line of text in the [[Text TOP]] or [[Text SOP]], after it has been formatted. Contains various members about the line such as it's text, position etc.'"""
	glyph : int
	"""The index of the glyph that represents this text line."""
	fontIndex : int
	"""The index of the font that the glyph belongs to. Glyphs are not interchangable between fonts."""
	text : str
	"""The text for this line."""
	origin : tdu.Position
	"""A tdu.Position object that gives the baseline origin of the line of text."""
	lineWidth : float
	"""The width of the format box of this line of text."""
	par : parameter.TextLine
	"""Parameters of parameter.TextLine"""
	pass


class tdu():
	"""The ```tdu</code> module is a generic utility module containing all miscellaneous functions that don't refer specifically to TouchDesigner data structures.  <code>tdu``` is imported by default when the application launches."""
	fileTypes : dict
	"""A dictionary of all supported file types, organized by category.

```python


# example of various file types accepted by Movie File In TOP

tdu.fileTypes['movie']

tdu.fileTypes['image']


```


```python


# other file types

tdu.fileTypes['audio']


```


Note: Acceptable file types can be both uppercase and lowercase, so if ```suffix</code> is a suffix string, you need to force it to lowercase by using <code>suffix.lower()```:

```python


for suffix.lower() in tdu.fileTypes['movie']:

	print(suffix)


```
"""
	Matrix : tdu.Matrix
	"""The [[Matrix Class|Matrix]] definition class."""
	Position : tdu.Position
	"""The [[Position Class|Position]] definition class."""
	Vector : tdu.Vector
	"""The [[Vector Class|Vector]] definition class."""
	Quaternion : tdu.Quaternion
	"""The [[Quaternion Class|Quaternion]] definition class."""
	Color : tdu.Color
	"""The [[Color Class|Color]] definition class."""
	Dependency : tdu.Dependency
	"""The [[Dependency Class|Dependency]] definition class."""
	FileInfo : tdu.FileInfo
	"""The FileInfo object takes a file path and has a few utility properties to provide additional information. It is derived from str, so will work as a Python string, but can be differentiated from a regular string by using ```isinstance(tdu.FileInfo)```.

Utility properties include:

* path: filepath string

* ext: string after and including '.'

* fileType: the TD filetype (from tdu.fileTypes)

* absPath: the absolute path to filepath

* dir: the containing directory of filepath

* exists: exists in file-system

* isDir: is a directory in the file-system

* isFile: is a file in the file-system

* baseName: the name of the final element in the path"""
	ArcBall : tdu.ArcBall
	"""The [[ArcBall Class|ArcBall]] definition class."""
	Camera : tdu.Camera
	"""The [[Camera Class|Camera]] definition class."""
	debug : module
	"""Helper module for the builtin debug statement. [[Debug_module|Documentation.]]"""
	par : parameter.tdu
	"""Parameters of parameter.tdu"""
	def rand(self, seed) -> float: 
		"""Return a random value in the range [0.0, 1.0) given the input seed value. That is, it will never return 1.0, but it may return 0.0. For a given seed, it will always return the same random number. The seed does not need to be a number. If the seed is not numeric, it resolves it to its string representation to produce a unique value. In the case of OPs for example, its string representation is a constant path. Thus one can produce a unique random value for each OP which remains the same for that OP each time you reload TouchDesigner.

```python


tdu.rand(me) # return a specific random number based on path

tdu.rand(5) # return a specific random number

tdu.rand(absTime.frame) # return a different number every frame


```"""
		pass
	def clamp(self, inputVal, min, max) -> any: 
		"""Returns the input value clamped between min and max values. Arguments can be any type that can be compared (float, int, str, etc)."""
		pass
	def remap(self, inputVal, fromMin, fromMax, toMin, toMax) -> float: 
		"""Returns the input value remapped from the first range to the second.

```python


tdu.remap(0.5, 0, 1,  -180, 180)  #remap slider value to angle range


```"""
		pass
	def base(self, str) -> str: 
		"""Returns the beginning portion of the string occurring before any digits. The search begins after the last slash if any are present.

* str - The string to extract the base name from.

```python


tdu.base('arm123') # returns 'arm'

tdu.base('arm123/leg456') # returns 'leg'


```


Note this method will work on any string, but when given a specific operator, its more efficient to use its local base member:

```python


n = op('arm123/leg456')

b = n.base #returns 'leg'


```"""
		pass
	def digits(self, str) -> int or None: 
		"""Returns the numeric value of the last consecutive group of digits in the string, or None if not found. The search begins after the last slash if any are present. The digits do not nessearily need to be at the end of the string.

```python


tdu.digits('arm123') # returns 123

tdu.digits('arm123/leg456') # returns 456

tdu.digits('arm123/leg') # returns None, searching is only done after the last /

tdu.digits('arm123/456leg') # returns 456


```


Note this method will work on any string, but when given a specific operator, its more efficient to use its local digits member:

```python


n = op('arm123/leg456')

d = n.digits # returns 456


```"""
		pass
	def validName(self, str) -> str: 
		"""Returns a version of the string suitable for an operator name. Converts illegal characters to underscores.

    Slashes are converted to underscores. To preserve forward slashes, use validPath() instead.

```python


tdu.validName('a#bc def') # returns 'a_bc_def'


```"""
		pass
	def validPath(self, str) -> str: 
		"""Returns a version of the string suitable for an operator path, including slashes. Converts illegal characters to underscores.

```python


tdu.validPath('/a#bc d/ef') # returns '/a_bc_d/ef'


```"""
		pass
	def expand(self, pattern) -> list: 
		"""Return a list of the expanded items, following the rules of [[Pattern Expansion]].

```python


tdu.expand('A[1-3] B[xyz]') # return ['A1', 'A2', 'A3', 'Bx', 'By', 'Bz']


```"""
		pass
	def expandPath(self, path) -> str: 
		"""Expand the file path, using project.paths, the current folder, and any other relevant information.

```python


tdu.expandPath('movies:/test.bmp') # looks at project.paths for 'movies' entry.


```"""
		pass
	def collapsePath(self, path, asExpression=False) -> str: 
		"""Collapse the file path, using project.paths, the current folder, and any other relevant information.

```python


tdu.collapsePath('C:/downloads/test.bmp') # looks at project.paths for any entries matching the path, and removes current folder from prefix.


```


* path - The path to be shortened.

* asExpression  - (Keyword, Optional) If True, result can be used as an expression, including [[App Class]] members and quoted strings."""
		pass
	def split(self, string, eval=False) -> list: 
		"""Return a list from a space separated string, allowing quote delimiters.

* string - Any Python object, as it will be evaluated as str(string). Parameters will work.

* eval - (Keyword, Optional) If True convert any valid Python literal structures: strings, numbers, tuples, lists, dicts, booleans, and None.

```python


split('1 2.3 None fred 'one \'2\'' '[1,2]'') #yields ['1', '2.3', 'None', 'fred', 'one '2'', '[1, 2]']

split('1 2.3 None fred 'one \'2\'' '[1,2]'', True) #yields [1, 2.3, None, 'fred', 'one '2'', [1, 2]]


```"""
		pass
	def match(self, pattern, inputList, caseSensitive=True) -> list: 
		"""Return a subset of inputList, in which each element matches the pattern. Wildcards are supported.

```python
tdu.match('foo* ', ['foo', 'bar']) # return ['foo']

tdu.match('ba?', ['foo', 'bar']) # return ['bar']
```"""
		pass
	def calibrateCamera(self, ) -> None: 
		"""Returns a set of values based on the input calibration data. This Method is not necessary anymore due to the inclusion of [[openCV]] in TouchDesigner. Refer to [http://docs.opencv.org/3.1.0/d4/d94/tutorial_camera_calibration.html OpenCV Documentation]"""
		pass
	def forceCrash(self, ) -> None: 
		"""forces a crash for debugging and crash recovery purposes"""
		pass
	def tryExcept(self, func1, func2 or val) -> any: 
		"""Evaluate the first function (func1). If an exception is raised, return second argument instead. Second argument can be either a function that is a called, or a final result. '''Note:''' If the second argument is a function, it is only called if the first function fails.



This is a one-liner try/except function for use in parameter expressions to handle simple errors. '''Tip:''' always be careful when hiding errors with try/except, because it can make real problems in your code/network invisible.

```python


    tdu.tryExcept(lambda: 1/me.par.w, 0.0) # second argument is simply 0.0

    tdu.tryExcept(lambda: 1/me.par.w, me.GetDefaultValue)   # Good:  me.GetDefaultValue not called until needed.

    tdu.tryExcept(lambda: 1/me.par.w, me.GetDefaultValue()) # >> INCORRECT <<.  Always calls second function even if not needed.
```"""
		pass
	def ParMenu(self, menuNames, menuLabels=None) -> any: 
		"""This method uses a list of strings to create an object meant to be used as a [[Par Class|parameter]] menu source.

* menuNames - A list of strings for menu values.

* menuLabels - (Optional) A list of strings for menu labels. Defaults to menuNames."""
		pass
	def TableMenu(self, table, nameCol=0, labelCol=None, includeFirstRow=False) -> any: 
		"""Create a parameter menu source object based on a DAT table.



This method uses a table to create an object meant to be used as a [[Par Class|parameter]] menu source.

* table - a DAT table to get the menu information from

* nameCol - (Keyword, Optional) Column name or number for menuNames. Defaults to 0.

* labelCol - (Keyword, Optional) Column name or number for menuLabels. Defaults to None, which means to use names as labels.

* includeFirstRow - (Keyword, Optional) if True, include first row of table in menu entries. Defaults to False.



Generally you will use this in the menuSource field in the Component Editor as follows

```python


    tdu.TableMenu(op('table1')) # use the first column of table1 as a list of menu names and labels

    tdu.TableMenu(op('table2'), nameCol='names', labelCol='labels') # from table2, use the column labeled 'names' as menu names, and the column labeled 'labels' as menu names

    tdu.TableMenu(op('table3'), labelCol=1, includeFirstRow=True) # from table3, use the first column as menu names and the second column as menu labels. Include the first row of the table in those lists


```"""
		pass
	pass


class SysInfo():
	"""The SysInfo class describes current system information. '''Note:''' It can be accessed with the <syntaxhighlight lang=python inline=true>sysinfo</syntaxhighlight> object, found in the automatically imported [[td Module|td module]].

```python


# return the amount of available ram

sysinfo.ram


```
"""
	numCPUs : int
	"""The number of CPUs/cores on the system."""
	ram : float
	"""Amount of available RAM memory."""
	numMonitors : int
	"""The number of monitors."""
	xres : int
	"""The system's current monitor resolution width."""
	yres : int
	"""The system's current monitor resolution height."""
	tfs : str
	"""The path to the TFS directory."""
	MIDIInputs : list of str
	"""A list of all MIDI Input device names."""
	MIDIOutputs : list of str
	"""A list of all MIDI Output device names."""
	par : parameter.SysInfo
	"""Parameters of parameter.SysInfo"""
	pass


class Segment():
	"""A Segment object describes a single segment from a Timer CHOP."""
	beginFrames : int
	"""The beginning point of the segment expressed in frames."""
	beginSamples : int
	"""The beginning point of the segment expressed in samples."""
	beginSeconds : float
	"""The beginning point of the segment expressed in seconds."""
	custom : oDict
	"""Ordered dictionary of all the extra column values associated with the segment."""
	cycle : bool
	"""Whether or not the segment will repeat itself."""
	cycleEndAlertFrames : int
	"""The amount of time before cycling the callback will be executed, expressed in frames."""
	cycleEndAlertSamples : int
	"""The amount of time before cycling the callback will be executed, expressed in samples."""
	cycleEndAlertSeconds : float
	"""The amount of time before cycling the callback will be executed, expressed in seconds."""
	cycleLimit : bool
	"""Whether or not the segment will repeat itself indefinitely."""
	delayFrames : int
	"""The delay portion of the segment expressed in frames."""
	delaySamples : int
	"""The delay portion of the segment expressed in samples."""
	delaySeconds : float
	"""The delay portion of the segment expressed in seconds."""
	lengthFrames : int
	"""The length portion of the segment expressed in frames."""
	lengthSamples : int
	"""The length portion of the segment expressed in samples."""
	lengthSeconds : float
	"""The length portion of the segment expressed in seconds."""
	maxCycles : int
	"""The maximum number of repetitions."""
	owner : op
	"""The OP to which this object belongs."""
	row : int
	"""Named tuple of all the parameter or column values describing the segment."""
	speed : float
	"""The speed multiplier of the segment."""
	index : int
	"""The numeric index of this segment."""
	par : parameter.Segment
	"""Parameters of parameter.Segment"""
	pass


class Runs():
	"""The Runs class describes the set of all delayed [[Run Class|run objects]]. It can be accessed with the runs object, found in the automatically imported [[td Module|td module]]. See [[Run Command Examples]] for more info.

```python


print(len(runs))	# number of active run objects 

print(runs[0])		# first run object

for r in runs:

	r.kill()		# kill all run objects


```
"""
	par : parameter.Runs
	"""Parameters of parameter.Runs"""
	pass


class Quaternion():
	"""Holds a Quaternion object which can be used to manipulate rotations in various ways. Quaternions can be constructed using a few different ways to describe the initial rotation:



```python


# From Euler Angles

q = tdu.Quaternion(tdu.Vector(30, 5, -5))

# From an angle and a rotation axis

q = tdu.Quaternion(30, tdu.Vector(0, 1, 0))

# From two vectors, rotate from the first vector to the second vector

q = tdu.Quaternion(tdu.Vector(1, 0, 0), tdu.Vector(0, 1, 0))

# From a set of 4 quaternion values

q = tdu.Quaternion(x, y, z, w)




```




Quaternions can be used like simple Python lists:

```python


print(q[1])		# same as q.y

q[2] = 0		# same as q.z


```




See also [[Transform CHOP]] which accepts, manipulates and outputs quaternions as sets of CHOP channels."""
	x : float
	"""Get or set the x component of the quaternion."""
	y : float
	"""Get or set the y component of the quaternion."""
	z : float
	"""Get or set the z component of the quaternion."""
	w : float
	"""Get or set the w component of the quaternion."""
	par : parameter.Quaternion
	"""Parameters of parameter.Quaternion"""
	def lerp(self, q2, factor) -> any: 
		"""Returns the linear interpolation of the quaternion with another quaternion and an interpolation factor.

The quaternion argument can be anything from which a quaternion can be derived ie. (x,y,z,w), Matrix, etc.

The interpolation factor must be between 0 and 1.

```python


q3 = q.lerp(q2, factor)


```"""
		pass
	def length(self, ) -> float: 
		"""Returns the length of the quaternion.

```python


l = q.length()


```"""
		pass
	def cross(self, q2) -> any: 
		"""Returns the cross product of the quaternion and argument.

The quaternion argument can be anything from which a quaternion can be derived ie. (x,y,z,w), Matrix, etc.

```python


l = q.cross(q2)


```"""
		pass
	def rotate(self, vec) -> any: 
		"""Rotates a vector using the current quaternion. Returns a new vector.

```python


v2 = q.rotate(v1)


```"""
		pass
	def slerp(self, q2, factor) -> any: 
		"""Returns the spherical interpolation of the quaternion with another quaternion and an interpolation factor.

The quaternion argument can be anything from which a quaternion can be derived ie. (x,y,z,w), Matrix, etc.

```python


q3 = q.slerp(q2, factor)


```"""
		pass
	def eulerAngles(self, order='xyz') -> tuple: 
		"""Returns euler angles in degrees as a tuple (i.e. pitch as x, yaw as y, roll as z) from current quaternion and a rotation order. The 'order' argument can be set to any valid rotation order which by default is set to 'xyz'.

```python


r = q.eulerAngles(order='xyz')


```"""
		pass
	def fromEuler(self, order='xyz') -> tuple: 
		"""Returns and set the current quaternion from euler angles in degrees as a 3 inputs argument (i.e. pitch as x, yaw as y, roll as z). The 'order' argument can be set to any valid rotation order which by default is set to 'xyz'.

```python
r = q.fromEuler(order='xyz')
```"""
		pass
	def axis(self, ) -> any: 
		"""Returns the rotation axis vector of the quaternion.

```python


v = q.axis()


```"""
		pass
	def dot(self, q2) -> float: 
		"""Returns the dot product of the quaternion and the argument.

The quaternion argument can be anything from which a quaternion can be derived ie. (x,y,z,w), Matrix, etc.

```python


l = q.dot(q2)


```"""
		pass
	def exp(self, ) -> any: 
		"""Returns the exponential of the quaternion as a new quaternion.

```python


q2 = q.exp()


```"""
		pass
	def copy(self, ) -> any: 
		"""Creates a copy of the quaternion with separate values."""
		pass
	def log(self, ) -> any: 
		"""Returns the natural logarithm of the current quaternion as a new quaternion.

```python


l = q.log()


```"""
		pass
	def inverse(self, ) -> None: 
		"""Invert the quaternion in place.

```python


q.inverse()


```"""
		pass
	def angle(self, ) -> float: 
		"""Returns the rotation angle (in degrees) of the quaternion.

```python


a = q.angle()


```"""
		pass
	def Quaternion *= Quaternion -> Quaternion: 
		"""Applies the rotation of one quaternion to another quaternion.

```python


# apply rotation of q2 to q1

q1 * = q2


```"""
		pass
	pass


class ProductEntry():
	"""A class to interact with a dongle entry for a single dongle connected to the system."""
	licenseType : int
	"""Returns the license type for this product entry on the dongle."""
	updateDate : tuple(YYYY, MM, DD)
	"""The date the product entry is valid until. Returns a tuple in the form (YYYY, MM, DD)."""
	version : str
	"""The version of TouchDesigner this dongle product entry is valid for."""
	par : parameter.ProductEntry
	"""Parameters of parameter.ProductEntry"""
	pass


class Preferences():
	"""The Preferences class describes the set of configurable preferences that are retained between sessions. It can be accessed with the ui.preferences object or through the [[Dialogs:Preferences_Dialog|Preferences Dialog]]."""
	defaults : dict
	"""A dictionary of preferences with their default values."""
	par : parameter.Preferences
	"""Parameters of parameter.Preferences"""
	def save(self, ) -> None: 
		"""Save preference values to disk.  Unless saved, changes to preferences will be lost, next time application is started."""
		pass
	def resetToDefaults(self, ) -> None: 
		"""Reset all preferences to their default values."""
		pass
	def load(self, ) -> None: 
		"""Restore preference values from disk."""
		pass
	def len(self, Preferences) -> int: 
		"""Returns the total number of preferences.

```python


a = len(ui.preferences)


```"""
		pass
	def [<preference name>] -> any: 
		"""Get or set specific preference given a preference name key.

```python


v = ui.preferences['dats.autoindent']

ui.preferences['dats.autoindent'] = 0


```"""
		pass
	def Iterator -> str: 
		"""Iterate over each preference name.

```python


for p in ui.preferences:

        print(p) # print the name of all preferences


```"""
		pass
	pass


class Position():
	"""The position class holds a single 3 component position. A position is a single point in space, and it's important to use a position or [[Vector Class|vector]] as appropriate for the data that is being calculated, since matrix operations on them will end in different results. When being multiplied by a [[Matrix Class|Matrix]], this class will implicitly have a 4th component (W component) of 1. If the Matrix is a projection matrix that will cause the W component to become something other than 1, all 4 components will be divided by W to make the position homogeneous again. A new position can be created without any arguments, with 3 arguments for the x,y,z values, or with a single argument which is a variable that has 3 entries such as a list of length 3, or another position or vector.





Examples of creating a position:

```python


p = tdu.Position() # starts as (0, 0, 0)

p2 = tdu.Position(1, 5, 0)

values = [0, 1, 0]

p3 = tdu.Position(values)


```
"""
	x : float
	"""Gets or sets the X component of the position."""
	y : float
	"""Gets or sets the Y component of the position."""
	z : float
	"""Gets or sets the Z component of the position."""
	par : parameter.Position
	"""Parameters of parameter.Position"""
	def translate(self, x, y, z) -> None: 
		"""Translates the position by the specified values.

* x, y, z - The values to translate by.

```python


p.translate(5, 2, 0)


```"""
		pass
	def scale(self, x, y, z) -> None: 
		"""Scales each component of the position by the specified values.

* x, y, z - The values to scale each component of the position by.

```python


p.scale(1, 2, 1)


```"""
		pass
	def copy(self, ) -> any: 
		"""Returns a new position that is a copy of the position.

```python


newV = v.copy()


```"""
		pass
	pass


class ParGroupUnit():
	"""The ParGroupUnit class describes a subclass of a [[ParGroup Class|ParGroup]] ending with a unit parameter. See also Custom ParGroup."""
	unit : par
	"""The unit parameter in this ParGroupUnit object."""
	par : parameter.ParGroupUnit
	"""Parameters of parameter.ParGroupUnit"""
	pass


class ParGroupPulse():
	"""The ParGroupPulse class describes a subclass of a ParGroup ending with a pulse parameter. See also Custom ParGroup."""
	par : parameter.ParGroupPulse
	"""Parameters of parameter.ParGroupPulse"""
	def pulse(self, value, frames=nframes, seconds=nseconds) -> None: 
		"""Pulsing sets a parameter to the specific value, cooks the operator, then restores the parameter to its previous value.

For pulse type parameters no value is specified or used.

*  value - (Optional) The tuple to pulse this parGroup with, default is <syntaxhighlight lang=python inline=true>[1]</syntaxhighlight>.

*  frames - (Optional) Number of frames before restoring the parameter to its original value.

*  seconds - (Optional) Number of seconds before restoring the parameter to its original value.

```python


op('moviein1').parGroup.reload.pulse([1]) # set the reload toggle, then cook

op('glsl1').parGroup.loadvariablenames.pulse() # activate the pulse parameter

op('geo1').parGroup.t.pulse([0,2,0], frames=120) # pulse geometry transform for 120 frames

op('text1').parGroup.text.pulse(['GO!'], seconds=3) # pulse text TOP string field, for 3 seconds

op('noise').parGroup.type.pulse(['random'], seconds=0.5) # pulse noise menu type for half a second


```"""
		pass
	pass


class Panes():
	"""The Panes class describes the list of all [[Pane Class|pane objects]].  It can be accessed from [[UI Class|ui.panes]]."""
	current : td.Pane
	"""The currently selected [[Pane Class|pane]]."""
	par : parameter.Panes
	"""Parameters of parameter.Panes"""
	def createFloating(self, type=PaneType.NETWORKEDITOR, name=None, maxWidth=1920, maxHeight=1080, monitorSpanWidth=0.9, monitorSpanHeight=0.9) -> any: 
		"""Return a floating pane.

* type - (Keyword, Optional) Type of pane created. See [[Pane Class|Pane]] for examples.

* name - (Keyword, Optional) Name of the pane.  This value can be used to find the pane in ui.panes.

* maxWidth - (Keyword, Optional) Upper limit on the width of the created window. Specified in pixels.

* maxHeight - (Keyword, Optional) Upper limit on the height of the created window. Specified in pixels.

* monitorSpanWidth - (Keyword, Optional) Specifies window width as a portion of the monitor width.

* monitorSpanHeight - (Keyword, Optional) Specifies window height as a portion of the monitor height.

Example

```python


    p = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name='Output')

    p.owner = op('/project1/base1')


```"""
		pass
	def len(self, Panes) -> int: 
		"""Returns the total number of panes.

```python


a = len(ui.panes)


```"""
		pass
	def [index] -> any: 
		"""Get specific pane, referenced by string or index.

```python


p = ui.panes[0]

p = ui.panes['pane1']


```"""
		pass
	def Iterator -> any: 
		"""Iterate over each pane.

```python


for n in ui.panes:

        # do something with n


```"""
		pass
	pass


class Options():
	"""The Options class describes the set of configurable UI options.  It can be accessed with the ui.options object."""
	par : parameter.Options
	"""Parameters of parameter.Options"""
	def resetToDefaults(self, ) -> None: 
		"""Reset all options to their default values."""
		pass
	def len(self, Options) -> int: 
		"""Returns the total number of options.

```python


a = len(ui.options)


```"""
		pass
	def [<option name>] -> any: 
		"""Get or set specific option given an option name key.

```python


v = ui.options['DAT.width']

ui.options['DAT.width'] = 50


```"""
		pass
	def Iterator -> str: 
		"""Iterate over each option name.

```python


for n in ui.options:

        print(n) # print the name of all options


```"""
		pass
	pass


class OP():
	"""The OP class defines a reference to a single [[Operator|operator]]."""
	valid : bool
	"""True if the referenced operator currently exists, False if it has been deleted."""
	id : int
	"""Unique id for the operator. This id can also be passed to the op() and ops() methods. Id's are not consistent when a file is re-opened, and will change if the OP is copied/pasted, changes OP types, deleted/undone. The id will not change if the OP is renamed though. Its data type is integer."""
	name : str
	"""Get or set the operator name."""
	path : str
	"""Full path to the operator."""
	digits : int
	"""Returns the numeric value of the last consecutive group of digits in the name, or None if not found. The digits can be in the middle of the name if there are none at the end of the name."""
	base : str
	"""Returns the beginning portion of the name occurring before any digits."""
	passive : bool
	"""If true, operator will not cook before its access methods are called.  To use a passive version of an operator n, use passive(n)."""
	curPar : td.Par
	"""The parameter currently being evaluated. Can be used in a parameter expression to reference itself."""
	time : OP
	"""[[timeCOMP Class|Time Component]] that defines the operator's time reference."""
	ext : class
	"""The object to search for parent [[Extensions|extensions]].

```'python'


me.ext.MyClass


```
"""
	mod : mod
	"""Get a [[MOD Class|module on demand]] object that searches for DAT modules relative to this operator."""
	pages : list
	"""A list of all built-in pages."""
	parGroup : tuple
	"""An intermediate [[ParGroupCollection Class|parameter collection]] object, from which a specific [[ParGroup Class|parameter group]] can be found.

```'python'


n.parGroup.t

# or

n.parGroup['t']


```
"""
	par : td.Par
	"""An intermediate [[ParCollection Class|parameter collection]] object, from which a specific [[Par Class|parameter]] can be found.

```'python'


n.par.tx

# or

n.par['tx']


```
"""
	builtinPars : list or par
	"""A list of all [[Par Class|built-in parameters]]."""
	customParGroups : list of parGroups
	"""A list of all [[ParGroup Class|ParGroups]], where a ParGroup is a set of parameters all drawn on the same line of a dialog, sharing the same label."""
	customPars : list of par
	"""A list of all [[Par Class|custom parameters]]."""
	customPages : list
	"""A list of all [[Page Class|custom pages]]."""
	customTuplets : list
	"""A list of all parameter tuplets, where a tuplet is a set of parameters all drawn on the same line of a dialog, sharing the same label."""
	replicator : OP or None
	"""The [[replicatorCOMP Class|replicatorCOMP]] that created this operator, if any."""
	storage : dict
	"""[[Storage]] is dictionary associated with this operator. Values stored in this dictionary are persistent, and saved with the operator. The dictionary attribute is read only, but not its contents. Its contents may be manipulated directly with methods such as OP.fetch() or OP.store() described below, or examined with an [[Examine DAT]]."""
	tags : list
	"""Get or set a set of user defined strings. [[Tag|Tags]] can be searched using OP.findChildren() and the [[OP Find DAT]].

The set is a regular python set, and can be accessed accordingly:

```'python'


n.tags = ['effect', 'image filter']

n.tags.add('darken')


```
"""
	children : list
	"""A list of [[OP Class|operators]] contained within this operator. Only [[COMP Class|component]] operators have children, otherwise an empty list is returned."""
	numChildren : int
	"""Returns the number of children contained within the operator. Only [[COMP Class|component]] operators have children."""
	numChildrenRecursive : int
	"""Returns the number of operators contained recursively within this operator. Only [[COMP Class|component]] operators have children."""
	op : OP or None
	"""The operator finder object, for accessing operators through paths or shortcuts. '''Note:''' a version of this method that searches relative to '/' is also in the global [[td Module|td module]].



```'''op(pattern1, pattern2..., includeUtility=False)'''</code> &rarr; <code class='return'>[[OP Class|OP]] or None```

<blockquote>

Returns the first OP whose path matches the given pattern, relative to the inside of this operator. Will return None if nothing is found. Multiple patterns may be specified which are all added to the search. Numeric OP ids may also be used.

*  ```pattern``` - Can be string following the [[Pattern Matching]] rules, specifying which OP to return, or an integer, which must be an OP Id. Multiple patterns can be given, the first matching OP will be returned.

*  ```includeUtility``` '''(Optional)''' - if True, allow [[Network_Utilities:_Comments,_Network_Boxes,_Annotates|Utility nodes]] to be returned. If False, Utility operators will be ignored.



```'python'


b = op('project1')

b = op('foot* ', 'hand* ') #comma separated

b = op('foot*  hand* ')  #space separated

b = op(154)


```


</blockquote>

```'''op.shortcut'''</code> &rarr; <code>OP```

<blockquote>

:An operator specified with by a [[Global OP Shortcut]]. If no operator exists an exception is raised. These shortcuts are global, and must be unique. That is, cutting and pasting an operator with a Global OP Shortcut specified will lead to a name conflict. One shortcut must be renamed in that case. Furthermore, only components can be given Global OP Shortcuts.

: * ```shortcut``` - Corresponds to the Global OP Shortcut parameter specified in the target operator.

```'python'


b = op.Videoplayer 


```


To list all Global OP Shortcuts:

```'python'


for x in op:

	print(x)


```


</blockquote>"""
	parent : OP
	"""The [[Parent Shortcut|Parent Shortcut]] object, for accessing parent components through indices or shortcuts.

'''Note:''' ''a version of this method that searches relative to the current operator is also in the global [[td Module|td module]].''



<code class='python'>parent(n)</code> &rarr; <code class='return'>OP or None</code>

<blockquote>

The nth parent of this operator. If n not specified, returns the parent. If n = 2, returns the parent of the parent, etc. If no parent exists at that level, None is returned.

* n - (Optional) n is the number of levels up to climb. When n = 1 it will return the operator's parent.

```'python'


p = parent(2) #grandfather


```


</blockquote>

<code class='python'>parent.shortcut</code> &rarr; <code class='return'>OP</code>

<blockquote>

A parent component specified with a shortcut. If no parent exists an exception is raised.

* shortcut - Corresponds to the [[Parent Shortcut]] parameter specified in the target parent.

```'python'


n = parent.Videoplayer


```


See also Parent Shortcut for more examples.</blockquote>"""
	iop : OP
	"""The Internal Operator Shortcut object, for accessing internal shortcuts. See also [[Internal Operators]].



'''Note:''' a version of this method that searches relative to the current operator is also in the global [[td Module]]."""
	ipar : OP
	"""The Internal Operator Parameter Shortcut object, for accessing internal shortcuts.  See also [[Internal Parameters]].

    

'''Note:''' a version of this method that searches relative to the current operator is also in the global [[td Module]]."""
	currentPage : [[Page Class|Page]]
	"""Get or set the currently displayed parameter page. It can be set by setting it to another page or a string label.

```'python'
n.currentPage = 'Common'
```
"""
	activeViewer : bool
	"""Get or set [[Viewer Active Flag]]."""
	allowCooking : bool
	"""Get or set [[Cooking Flag]]. Only COMPs can disable this flag."""
	bypass : bool
	"""Get or set [[Bypass Flag]]."""
	cloneImmune : bool
	"""Get or set [[Immune Flag|Clone Immune Flag]]."""
	current : bool
	"""Get or set [[Current Flag]]."""
	display : bool
	"""Get or set [[Display Flag]]."""
	expose : bool
	"""Get or set the [[Expose Flag]] which hides a node from view in a network."""
	lock : bool
	"""Get or set [[Lock Flag]]."""
	selected : bool
	"""Get or set [[Selected Flag]]. This controls if the node is part of the network selection. (yellow box around it)."""
	python : bool
	"""Get or set parameter expression language as python."""
	render : bool
	"""Get or set [[Render Flag]]."""
	showCustomOnly : bool
	"""Get or set the Show Custom Only Flag which controls whether or not non custom parameters are display in[[Parameter Dialog | parameter dialogs]]."""
	showDocked : bool
	"""Get or set [[Docking|Show Docked Flag]]. This controls whether this node is visible or hidden when it is docked to another node."""
	viewer : bool
	"""Get or set [[Viewer Flag]]."""
	color : tuple(r, g, b)
	"""Get or set color value, expressed as a 3-tuple, representing its red, green, blue values. To convert between color spaces, use the built in colorsys module."""
	comment : str
	"""Get or set comment string."""
	nodeHeight : int
	"""Get or set node height, expressed in [[NetworkEditor Class|network editor]] units."""
	nodeWidth : int
	"""Get or set node width, expressed in [[NetworkEditor Class|network editor]] units."""
	nodeX : int
	"""Get or set node X value, expressed in [[NetworkEditor Class|network editor]] units, measured from its left edge."""
	nodeY : int
	"""Get or set node Y value, expressed in [[NetworkEditor Class|network editor]] units, measured from its bottom edge."""
	nodeCenterX : int
	"""Get or set node X value, expressed in [[NetworkEditor Class|network editor]] units, measured from its center."""
	nodeCenterY : int
	"""Get or set node Y value, expressed in [[NetworkEditor Class|network editor]] units, measured from its center."""
	dock : OP
	"""Get or set the [[OP Class|operator]] this operator is docked to.  To clear docking, set this member to None."""
	docked : list
	"""The (possibly empty) list of [[OP Class|operators]] docked to this node."""
	inputs : list
	"""List of input [[OP Class|operators]] (via left side connectors) to this operator. To get the number of inputs, use len(OP.inputs)."""
	outputs : list
	"""List of output [[OP Class|operators]] (via right side connectors) from this operator."""
	inputConnectors : list
	"""List of input [[Connector Class|connectors]] (on the left side) associated with this operator."""
	outputConnectors : list
	"""List of output [[Connector Class|connectors]] (on the right side) associated with this operator."""
	cookFrame : float
	"""Last frame at which this operator cooked."""
	cookTime : float
	"""'''Deprecated''' Duration of the last measured cook (in milliseconds)."""
	cpuCookTime : float
	"""Duration of the last measured cook in CPU time (in milliseconds)."""
	cookAbsFrame : float
	"""Last absolute frame at which this operator cooked."""
	cookStartTime : float
	"""Last offset from frame start at which this operator cook began, expressed in milliseconds."""
	cookEndTime : float
	"""Last offset from frame start at which this operator cook ended, expressed in milliseconds.  Other operators may have cooked between the start and end time.  See the cookTime member for this operator's specific cook duration."""
	cookedThisFrame : bool
	"""True when this operator has cooked this frame."""
	cookedPreviousFrame : bool
	"""True when this operator has cooked the previous frame."""
	childrenCookTime : float
	"""'''Deprecated''' The total accumulated cook time of all children of this operator during the last frame. Zero if the operator is not a [[COMP Class|COMP]] and/or has no children."""
	childrenCPUCookTime : float
	"""The total accumulated cook time of all children of this operator during the last frame. Zero if the operator is not a [[COMP Class|COMP]] and/or has no children."""
	childrenCookAbsFrame : float
	"""'''Deprecated''' The absolute frame on which childrenCookTime is based."""
	childrenCPUCookAbsFrame : float
	"""The absolute frame on which childrenCPUCookTime is based."""
	gpuCookTime : float
	"""Duration of GPU operations during the last measured cook (in milliseconds)."""
	childrenGPUCookTime : float
	"""The total accumulated GPU cook time of all children of this operator during the last frame. Zero if the operator is not a COMP and/or has no children."""
	childrenGPUCookAbsFrame : float
	"""The absolute frame on which childrenGPUCookTime is based."""
	totalCooks : int
	"""Number of times the operator has cooked."""
	cpuMemory : int
	"""The approximate amount of CPU memory this Operator is using, in bytes."""
	gpuMemory : int
	"""The amount of GPU memory this OP is using, in bytes."""
	type : str
	"""Operator type as a string. Example: 'oscin'."""
	subType : str
	"""Operator subtype. Currently only implemented for [[Component|components]]. May be one of: 'panel', 'object', or empty string in the case of base components."""
	OPType : str
	"""Python operator class type, as a string. Example: 'oscinCHOP'. Can be used with COMP.create() method."""
	label : str
	"""Operator type label. Example: 'OSC In'."""
	icon : str
	"""Get the letters used to create the operator's icon."""
	family : str
	"""Operator family. Example: CHOP. Use the global dictionary families for a list of each operator type."""
	isFilter : bool
	"""True if operator is a filter, false if it is a generator."""
	minInputs : int
	"""Minimum number of inputs to the operator."""
	maxInputs : int
	"""Maximum number of inputs to the operator."""
	isMultiInputs : bool
	"""True if inputs are ordered, false otherwise. Operators with an arbitrary number of inputs have unordered inputs, example [[Merge CHOP]]."""
	visibleLevel : int
	"""Visibility level of the operator. For example, expert operators have visibility level 1, regular operators have visibility level 0."""
	isBase : bool
	"""True if the operator is a Base (miscellaneous) [[Component|component]]."""
	isCHOP : bool
	"""True if the operator is a [[CHOP]]."""
	isCOMP : bool
	"""True if the operator is a [[Component|component]]."""
	isDAT : bool
	"""True if the operator is a [[DAT]]."""
	isMAT : bool
	"""True if the operator is a [[MAT|Material]]."""
	isObject : bool
	"""True if the operator is an [[object]]."""
	isPanel : bool
	"""True if the operator is a [[Panel]]."""
	isSOP : bool
	"""True if the operator is a [[SOP]]."""
	isTOP : bool
	"""True if the operators is a [[TOP]]."""
	licenseType : str
	"""Type of [[License Class|License]] required for the operator."""
	par : parameter.OP
	"""Parameters of parameter.OP"""
	def pars(self, pattern) -> list: 
		"""Returns a (possibly empty) list of [[Par Class|parameter objects]] that match the pattern.

* pattern - Is a string following the [[Pattern Matching]] rules, specifying which parameters to return.

```'python'


newlist = op('geo1').pars('t?', 'r?', 's?') #translate/rotate/scale parameters


```
Note: If searching for a single parameter given a name, it's much more efficient to use the subscript operator. For example:```'python'
name = 'MyName1'

op('geo1').par[name]
```"""
		pass
	def cook(self, force=False, recurse=False, includeUtility=False) -> None: 
		"""Cook the contents of the operator if required.

* force - (Keyword, Optional) If True, the operator will always cook, even if it wouldn't under normal circumstances.

* recurse - (Keyword, Optional) If True, all children and sub-children of the operator will be cooked.

* includeUtility - (Keyword, Optional) If specified, controls whether or not utility components (eg Comments) are included in the results."""
		pass
	def copyParameters(self, OP, custom=True, builtin=True) -> None: 
		"""Copy all of the parameters from the specified [[OP Class|operator]].  Both operators should be the same type.

* OP - The operator to copy.

* custom - (Keyword, Optional) When True, custom parameters will be copied.

* builtin - (Keyword, Optional) When True, built in parameters will be copied.

```'python'


op('geo1').copyParameters( op('geo2') )


```"""
		pass
	def changeType(self, OPtype) -> OP: 
		"""Change referenced operator to a new operator type.  After this call, this OP object should no longer be referenced.  Instead use the returned OP object.

* OPtype - The python class name of the operator type you want to change this operator to. This is not a string, but instead is a class defined in the global [[td Module|td module]].

```'python'


n = op('wave1').changeType(nullCHOP) #changes 'wave1' into a Null CHOP

n = op('text1').changeType(tcpipDAT) #changes 'text1' operator into a TCPIP DAT


```"""
		pass
	def dependenciesTo(self, OP) -> list: 
		"""Returns a (possibly empty) list of operator dependency paths between this operator and the specified operator. Multiple paths may be found."""
		pass
	def evalExpression(self, str) -> any: 
		"""Evaluate the expression from the context of this OP.  Can be used to evaluate arbitrary snippets of code from arbitrary locations.

* str - The expression to evaluate.

```'python'


op('wave1').evalExpression('me.digits')  #returns 1


```


If the expression already resides in a parameter, use that parameters [[Par Class|evalExpression()]] method instead."""
		pass
	def destroy(self, ) -> None: 
		"""Destroy the operator referenced by this OP. An exception will be raised if the OP's operator has already been destroyed."""
		pass
	def var(self, name, search=True) -> str: 
		"""Evaluate a[[Variables | variable]]. This will return the empty string, if not found. Most information obtained from variables (except for Root and Component variables) are accessible through other means in Python, usually in the global [[td Module|td module]].

* name - The variable name to search for.

* search - (Keyword, Optional) If set to True (which is default) the operator hierarchy is searched until a variable matching that name is found.  If false, the search is constrained to the operator."""
		pass
	def openMenu(self, x=None, y=None) -> None: 
		"""Open a node menu for the operator at x, y.  Opens at mouse if x & y are not specified.

* x - (Keyword, Optional) The X coordinate of the menu, measured in screen pixels.

* y - (Keyword, Optional) The Y coordinate of the menu, measured in screen pixels."""
		pass
	def relativePath(self, OP) -> str: 
		"""Returns the relative path from this operator to the OP that is passed as the argument.   See OP.shortcutPath for a version using expressions."""
		pass
	def setInputs(self, listOfOPs) -> None: 
		"""Set all the operator inputs to the specified list.

*  listOfOPs - A list containing one or more OPs. Entries in the list can be None to disconnect specific inputs.  An empty list disconnects all inputs."""
		pass
	def shortcutPath(self, OP, toParName=None) -> str: 
		"""Returns an expression from this operator to the OP that is passed as the argument. See OP.relativePath for a version using relative path constants.

*  toParName - (Keyword, Optional) Return an expression to this parameter instead of its operator."""
		pass
	def ops(self, pattern1, pattern2, *args, includeUtility=False) -> any: 
		"""Returns a (possibly empty) list of OPs that match the patterns, relative to the inside of this OP.

Multiple patterns may be provided. Numeric OP ids may also be used.

* pattern - Can be string following the [[Pattern Matching]] rules, specifying which OPs to return, or an integer, which must be an OP Id. Multiple patterns can be given and all matched OPs will be returned.

* includeUtility - (Keyword, Optional) If specified, controls whether or not utility components (eg Comments) are included in the results.

'''Note:''' a version of this method that searches relative to '/' is also in the global [[td Module|td module]].

```'python'


newlist = n.ops('arm* ', 'leg* ', 'leg5/foot* ')


```"""
		pass
	def addScriptError(self, msg) -> None: 
		"""Adds a script error to a node.

* msg - The error to add."""
		pass
	def addError(self, msg) -> None: 
		"""Adds an error to an operator.  Only valid if added while the operator is cooking. (Example Script SOP, CHOP, DAT).

* msg - The error to add."""
		pass
	def addWarning(self, msg) -> None: 
		"""Adds a warning to an operator.  Only valid if added while the operator is cooking. (Example Script SOP, CHOP, DAT).

* msg - The error to add."""
		pass
	def errors(self, recurse=False) -> str: 
		"""Get error messages associated with this OP.

* recurse - Get errors in any children or subchildren as well."""
		pass
	def warnings(self, recurse=False) -> str: 
		"""Get warning messages associated with this OP.

* recurse - Get warnings in any children or subchildren as well."""
		pass
	def scriptErrors(self, recurse=False) -> str: 
		"""Get script error messages associated with this OP.

* recurse - Get errors in any children or subchildren as well."""
		pass
	def clearScriptErrors(self, recurse=False, error='*') -> None: 
		"""Clear any errors generated during script execution.  These may be generated during execution of DATs, Script Nodes, Replicator COMP callbacks, etc.

* recurse - Clear script errors in any children or subchildren as well.

* error - Pattern to match when clearing errors

```'python'


op('/project1').clearScriptErrors(recurse=True)


```"""
		pass
	def childrenCPUMemory(self, ) -> int: 
		"""Returns the total CPU memory usage for all the children from this COMP."""
		pass
	def childrenGPUMemory(self, ) -> int: 
		"""Returns the total GPU memory usage for all the children from this COMP."""
		pass
	def resetNodeSize(self, ) -> None: 
		"""Reset the node tile size to its default width and height."""
		pass
	def closeViewer(self, topMost=False) -> None: 
		"""Close the floating content viewers of the OP.

* topMost - (Keyword, Optional) If True, any viewer window containing any parent of this OP is closed instead.

```'python'


op('wave1').closeViewer()

op('wave1').closeViewer(topMost=True) # any viewer that contains 'wave1' will be closed.


```"""
		pass
	def openViewer(self, unique=False, borders=True) -> None: 
		"""Open a floating content viewer for the OP.

* unique - (Keyword, Optional) If False, any existing viewer for this OP will be re-used and popped to the foreground. If unique is True, a new window is created each time instead.

* borders - (Keyword, Optional) If true, the floating window containing the viewer will have borders.

```'python'


op('geo1').openViewer(unique=True, borders=False) # opens a new borderless viewer window for 'geo1'


```"""
		pass
	def resetViewer(self, recurse=False) -> None: 
		"""Reset the OP content viewer to default view settings.

* recurse - (Keyword, Optional) If True, this is done for all children and sub-children as well.

```'python'


op('/').resetViewer(recurse=True) # reset the viewer for all operators in the entire file.


```"""
		pass
	def openParameters(self, ) -> None: 
		"""Open a floating dialog containing the operator parameters."""
		pass
	def fetch(self, key, default, search=True, storeDefault=False) -> any: 
		"""Return an object from the OP storage dictionary.  If the item is not found, and a default it supplied, it will be returned instead.

* key - The name of the entry to retrieve.

* default - (Optional) If provided and no item is found then the passed value/object is returned instead.

* storeDefault - (Keyword, Optional) If True, and the key is not found, the default is stored as well.

* search - (Keyword, Optional) If True, the parent of each OP is searched recursively until a match is found

```'python'


v = n.fetch('sales5', 0.0)


```"""
		pass
	def fetchOwner(self, key) -> OP: 
		"""Return the operator which contains the stored key, or None if not found.

* key - The key to the stored entry you are looking for.

```'python'


who = n.fetchOwner('sales5') #find the OP that has a storage entry called 'sales5'


```"""
		pass
	def store(self, key, value) -> any: 
		"""Add the key/value pair to the OP's storage dictionary, or replace it if it already exists.  If this value is not intended to be saved and loaded in the toe file, it can be be given an alternate value for saving and loading, by using the method storeStartupValue described below.

* key - A string name for the storage entry. Use this name to retrieve the value using fetch().

* value - The value/object to store.

```'python'


n.store('sales5', 34.5) # stores a floating point value 34.5.

n.store('moviebank', op('/project1/movies')) # stores an OP for easy access later on.


```"""
		pass
	def unstore(self, keys1, keys2, *args) -> None: 
		"""For key, remove it from the OP's storage dictionary. Pattern Matching is supported as well.

* keys - The name or pattern defining which key/value pairs to remove from the storage dictionary.

```'python'


n.unstore('sales* ') # removes all entries from this OPs storage that start with 'sales'


```"""
		pass
	def storeStartupValue(self, key, value) -> None: 
		"""Add the key/value pair to the OP's storage startup dictionary.  The storage element will take on this value when the file starts up.

* key - A string name for the storage startup entry.

* value - The startup value/object to store.

```'python'


n.storeStartupValue('sales5', 1) # 'sales5' will have a value of 1 when the file starts up.


```"""
		pass
	def unstoreStartupValue(self, keys1, keys2, *args) -> None: 
		"""For key, remove it from the OP's storage startup dictionary. Pattern Matching is supported as well.  This does not affect the stored value, just its startup value.

* keys - The name or pattern defining which key/value pairs to remove from the storage startup dictionary.

```'python'


n.unstoreStartupValue('sales* ') # removes all entries from this OPs storage startup that start with 'sales'


```"""
		pass
	def __getstate__(self, ) -> dict: 
		"""Returns a dictionary with persistent data about the object suitable for pickling and deep copies."""
		pass
	def __setstate__(self, ) -> dict: 
		"""Reads the dictionary to update persistent details about the object, suitable for unpickling and deep copies."""
		pass
	pass


class VFSFile():
	"""The VFSFile Class describes a virtual file contained within a [[Virtual File System]].<br>To access a virtual file in any operator's file parameter, use the virtual path as described below in the ```virtualPath``` member."""
	name : str
	"""Get or set the name of the file. This name can include slashes but should not include leading slashes."""
	size : int
	"""Get the size of the file data."""
	date : datetime
	"""Get the modified date of the file in the form of a datetime Python object."""
	virtualPath : str
	"""Get the virtual path of the file. Returns a String formatted for fetching the file data from VFS in operators such as the Movie File In TOP. Format is ```vfs:<path to owner>:<filename>```."""
	originalFilePath : str
	"""Get the original file path on disk. If the VFSFile was created from a bytearray and not a file on disk then this will be empty."""
	owner : OP
	"""Get the OP owner."""
	byteArray : bytearray
	"""Get or set the file data as a bytearray."""
	par : parameter.VFSFile
	"""Parameters of parameter.VFSFile"""
	def destroy(self, ) -> None: 
		"""Destroys the file in VFS referenced by this object."""
		pass
	def export(self, folder) -> str: 
		"""Exports the file to the specified folder on disk and returns the location.

* folder - The folder on disk to export the file to."""
		pass
	pass


class VFS():
	"""The VFS Class describes a COMP's [[Virtual File System|Virtual File System]]. <br>To access a virtual file in any operator's file parameter, use the virtual path format: ```vfs:<path to comp>:<filename>```. <br>[[VFSFile_Class]] does the file operators."""
	owner : OP
	"""Get the OP owner."""
	par : parameter.VFS
	"""Parameters of parameter.VFS"""
	def [name] -> VFSFile: 
		"""[[VFSFile Class|VFS Files]] may be easily accessed using the [] syntax.

* name - Must be an exact VFS file name. Wildcards are not supported. If not found, an error will be raised.

```python


p = op('base1').vfs['Banana.tif']


```"""
		pass
	def addByteArray(self, byteArray, name) -> VFSFile: 
		"""Add an embedded file from a bytearray to the component. Returns a VFSFile instance of the added file.  To delete the file, see ```destroy()``` on [[VFSFile Class]].

*  byteArray - A bytearray or bytes object representing the contents of the file.

*  name - The name of the file on VFS."""
		pass
	def addFile(self, filePath, overrideName=None) -> VFSFile: 
		"""Add an embedded file from disk to the component with an option to override the name. Returns a VFSFile instance of the added file. To delete the file, see ```destroy()``` on [[VFSFile Class]].

* filePath - The path of the file on disk to add.

* overrideName (Keyword, Optional) - When specified, will override the name of the file in VFS."""
		pass
	def export(self, folder, pattern='*', overwrite=False) -> list: 
		"""Exports any matching files to the folder on disk. If overwrite is True then any existing files on disks with the same name will be overwritten. Returns a list of paths on disk to the exported files.

* folder - The folder on disk to export the files to.

* pattern (Keyword, Optional) - The pattern to match names by.

* overwrite (Keyword, Optional) - When True, will overwrite any files that share the same name.

```python


# VFS contains one file with name 'A/B.tif'

COMP.vfs.export('C:/tmp') # returns ['C:/tmp/A/B.tif']


```"""
		pass
	def find(self, pattern='*') -> list: 
		"""Finds all files in VFS with names matching the pattern. Returns a list of VFSFile objects.

* pattern (Keyword, Optional) - The pattern to match names by."""
		pass
	def len(self, VFS) -> int: 
		"""Returns the total number of virtual files.

```python


a = len(op('base1').vfs)


```"""
		pass
	def Iterator -> str: 
		"""Iterate over each virtual file name.

```python


for f in op('base1').vfs:

        debug(f) # print info of all virtual files on base1


```"""
		pass
	pass


class Vertex():
	"""A Vertex describes an instance to a single geometry vertex, contained within a [[Prim Class|Prim]] object."""
	index : int
	"""The vertex position in its [[Prim Class|primitive]]."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	point : td.Point
	"""Get or set the [[Point Class|point]] to which the vertex refers."""
	prim : td.Prim
	"""The [[Prim Class|prim]] to which the vertex belongs."""
	par : parameter.Vertex
	"""Parameters of parameter.Vertex"""
	pass


class UI():
	"""The UI class describes access to the UI elements of the application, found in the automatically imported [[td Module|td module]].



To access members and methods of this class use the default instance ```ui```.



For Example:

```python


# open the Midi Device Mapper Dialog

ui.openMIDIDeviceMapper()


```
"""
	clipboard : str
	"""Get or set the operating system clipboard text contents."""
	colors : td.Colors
	"""Access to the application [[Colors Class|colors]]."""
	dpiBiCubicFilter : bool
	"""Get or set the global DPI scale filtering mode of TouchDesigner windows. True means bi-cubic, False means linear."""
	masterVolume : float
	"""Get or set the master audio output volume. A value of 0 is no output, while a value of 1 is full output."""
	options : td.Options
	"""Access to the application [[Options Class|options]]."""
	panes : td.Panes
	"""Access to the set of all [[Panes Class|panes]]."""
	performMode : bool
	"""Get or set [[Perform Mode]].  Set to True to go into Perform Mode, False to go into [[Designer Mode]]."""
	preferences : td.Preferences
	"""Access to the application [[Preferences Class|preferences]], which can also be access through the [[Preferences Dialog]]."""
	redrawMainWindow : bool
	"""Get or set whether the main window should redraw. The main window is either the main network editor, or the perform window."""
	rolloverOp : OP
	"""Operator currently under the mouse in a network editor."""
	rolloverPar : td.Par
	"""Parameter currently under the mouse in a parameter dialog."""
	rolloverPanel : panelCOMP
	"""returns the latest panel to get a rollover event. Takes into account click through, depth order, and other panel settings."""
	lastChopChannelSelected : td.Par
	"""Last [[Channel|CHOP channel]] selected via mouse."""
	showPaletteBrowser : bool
	"""Get or set display of the palette browser."""
	status : str
	"""Get or set the status message.

```python


ui.status = 'Operation Complete'


```
"""
	undo : td.Undo
	"""Acess to application undo functions."""
	windowWidth : int
	"""Get the app window width."""
	windowHeight : int
	"""Get the app window height."""
	windowX : int
	"""Get the app window X position."""
	windowY : int
	"""Get the app window Y position."""
	par : parameter.UI
	"""Parameters of parameter.UI"""
	def copyOPs(self, listOfOPs) -> None: 
		"""Copy a list of operators to the operator clipboard. All operators must be children of the same component.

* listOfOPs - A list containing one or more OPs to be copied.

```python
ui.copyOPs( op('geo1').selected )
```"""
		pass
	def pasteOPs(self, COMP, x=None, y=None) -> None: 
		"""Copy the contents of the operator clipboard into the specified component.

* COMP - The destination to receive the operators.

* x - Optional network coordinates at which to paste the operators.

* y - see x

```python
l = ui.pasteOPs( op('geo2') )
```"""
		pass
	def messageBox(self, title, message, buttons=['Ok']) -> int: 
		"""This method will open a message dialog box with the specified message.  Returns the index of the button clicked.

* title - Specifies the window title.

* message - Specifies the content of the dialog.

* buttons - (Keyword, Optional) Specifies a list button labels to show in the dialog.

```python


# basic usage

ui.messageBox('Warning', 'Have a nice day.')

# specify options and report result

a = ui.messageBox('Please select:', 'Buttons:', buttons=['a', 'b', 'c'])

ui.messageBox('Results', 'You selected item: ' + str(a))

# pick a node from their paths

ui.messageBox('Please select:', 'Nodes:', buttons=parent().children)

# pick a node from their first names (list comprehension)

ui.messageBox('Please select:', 'Nodes:', buttons=[x.name for x in parent().children])

# pick a cell

ui.messageBox('Please select:', 'Cells:', buttons=op('table1').cells('* ','* '))


```"""
		pass
	def refresh(self, ) -> None: 
		"""Update and redraw all viewports, nodes, UI elements etc immediately. This update is otherwise done once per frame at the end of all script executions. For example, if the current frame is manually changed during a script, a call to refresh will cause all dependent data to update immediately.

```python


for i in range(100):

        ui.status = str(i)

        ui.refresh()


```"""
		pass
	def chooseFile(self, load=True, start=None, fileTypes=None, title=None, asExpression=False) -> str or None: 
		"""Open a dialog box for loading or saving a file.  Returns the filename selected or None if the dialog is cancelled.

* load - (Keyword, Optional) If set to True, the dialog will be a Load dialog, otherwise it's a Save dialog.

* start - (Keyword, Optional) If provided, specifies an initial folder location and/or filename selection.

* fileTypes - (Keyword, Optional) If provided, specifies a list of file extensions that can be used as filters. Otherwise '* .* ' is the only filter.

* asExpression - (Keyword, Optional) If set to true, the results are provided as an expression, suitable for a [[Par Class|Parameter]] expression or as input to an eval() call.  [[App Class]] member constants such as samplesFolder may be included in the result.

* title (Keyword, Optional) If provided, will override the default window title.

```python


a = ui.chooseFile(start='python_examples.toe', fileTypes=['toe'], title='Select a toe') # specify extension

a = ui.chooseFile(fileTypes=tdu.fileTypes['image'], title='Select an image') # any support image extension

path = ui.chooseFile(load=False,fileTypes=['txt'],title='Save table as:')

if (path):

        op('table1').save(path)


```"""
		pass
	def chooseFolder(self, title=<nowiki>'Select Folder'</nowiki>, start=None, asExpression=False) -> str or None: 
		"""Open a dialog box for selecting a folder.  Returns the folder selected or None if the dialog is cancelled.

* title - (Keyword, Optional) If provided, specifies the window title.

* start - (Keyword, Optional) If provided, specifies an initial folder location and/or filename selection.

* asExpression - (Keyword, Optional) If set to true, the results are provided as an expression, suitable for a [[Par Class|Parameter]] expression or as input to an eval() call.  [[App Class]] member constants such as samplesFolder may be included in the result.

```python


a = ui.chooseFolder()

a = ui.chooseFolder(title='Select a folder location.')


```"""
		pass
	def viewFile(self, URL_or_path, showInFolder=False) -> None: 
		"""View a URL or file in the default external application. You can use ```ui.viewFile()``` to open a folder/directory in Windows Explorer or macOS Finder.

* URL_or_path - URL or path to launch.

```python


a = ui.viewFile('output.txt')


```


* showInFolder - Show file as selected in Explorer or macOS Finder instead of launching an external application.

```python


a = ui.viewFile('output.txt', showInFolder=True)


```"""
		pass
	def openAbletonControl(self, ) -> None: 
		"""Deprecated. Use [[TDAbleton]] instead."""
		pass
	def openBeat(self, ) -> None: 
		"""Open the [[Beat Dialog]]."""
		pass
	def openBookmarks(self, ) -> None: 
		"""Open the [[Bookmarks Dialog]]."""
		pass
	def openCOMPEditor(self, path) -> None: 
		"""Open component editor for the specific operator.

* path - Specifies the path to the operator.  An OP can be passed in as well."""
		pass
	def openConsole(self, ) -> None: 
		"""Open the [[Console Window]]."""
		pass
	def openDialogHelp(self, title) -> None: 
		"""Open help page for the specific dialog.

* title - Specifies the help page to open.

```python


ui.openDialogHelp('Window Placement Dialog')


```"""
		pass
	def openErrors(self, ) -> None: 
		"""Open the [[Errors Dialog]]."""
		pass
	def openExplorer(self, ) -> None: 
		"""Open an Explorer window."""
		pass
	def openExportMovie(self, path="") -> None: 
		"""Open the [[Export Movie Dialog]].

* path - Specifies the operator content to export."""
		pass
	def openHelp(self, ) -> None: 
		"""Open the [[Commands_and_Expressions|Help Dialog]]."""
		pass
	def openImportFile(self, ) -> None: 
		"""Open the [[Import File Dialog]]."""
		pass
	def openKeyManager(self, ) -> None: 
		"""Open the [[Key Manager Dialog]]."""
		pass
	def openMIDIDeviceMapper(self, ) -> None: 
		"""Open the [[MIDI Device Mapper Dialog]]."""
		pass
	def openNewProject(self, ) -> None: 
		"""Open the [[New Project Dialog]]."""
		pass
	def openOperatorSnippets(self, family=None, type=None, example=None) -> None: 
		"""Open the Operator Snippets window."""
		pass
	def openPaletteBrowser(self, ) -> None: 
		"""Open the [[Palette]]."""
		pass
	def openPerformanceMonitor(self, ) -> None: 
		"""Open the [[Performance Monitor Dialog]]."""
		pass
	def openPreferences(self, ) -> None: 
		"""Open the [[Preferences Dialog]]."""
		pass
	def openSearch(self, ) -> None: 
		"""Open the [[Search Replace Dialog]]."""
		pass
	def openTextport(self, ) -> None: 
		"""Open the [[Textport]]."""
		pass
	def openVersion(self, ) -> None: 
		"""Open a dialog displaying current version information.

See also: [[App Class|App.version]]"""
		pass
	def openWindowPlacement(self, ) -> None: 
		"""Open the [[Window Placement Dialog]]."""
		pass
	def findEditDAT(self, filename) -> any: 
		"""Given an external filename, finds the corresponding DAT thats update from this filename if any.."""
		pass
	pass


class TOP(OP):
	"""A [[TOP]] describes a reference to a TOP operator."""
	width : int
	"""Texture width, measured in pixels."""
	height : int
	"""Texture height, measured in pixels."""
	aspect : float
	"""Texture aspect ratio, width divided by height."""
	aspectWidth : float
	"""Texture aspect ratio, width."""
	aspectHeight : float
	"""Texture aspect ratio, height."""
	depth : int
	"""Texture depth, when using a 3 dimensional texture."""
	gpuMemory : int
	"""The amount of GPU memory this TOP is using, in bytes."""
	curPass : int
	"""The current cooking pass iteration, beginning at 0. The total can be set with the 'Passes' parameter on the operator's common page."""
	isTOP : bool
	"""True if the operators is a TOP."""
	par : parameter.TOP|parameter.OP
	"""Parameters of parameter.TOP & parameter.OP"""
	def sample(self, x=None,y=None,z=None,u=None,v=None,w=None) -> any: 
		"""Returns a 4-tuple representing the color value at the specified texture location. One horizontal and one vertical component must be specified. Note that this is a very expensive operation currently. It will always stall the graphics pipeline if the TOP is currently queued to get updated, and then downloads the entire texture (not just the requested pixel). Use this for debugging and non-realtime workflows only.

* x - (Keyword, Optional) The horizontal pixel coordinate to be sampled.

* y - (Keyword, Optional) The vertical pixel coordinate to be sampled.

* z - (Keyword, Optional) The depth pixel coordinate to be sampled. Available in builds 2022.23800 and later.

* u - (Keyword, Optional) The normalized horizontal coordinate to be sampled.

* v - (Keyword, Optional) The normalized vertical coordinate to be sampled.

* w - (Keyword, Optional) The normalized depth pixel coordinate to be sampled. Available in builds 2022.23800 and later.

```python


r = n.sample(x=25,y=100)[0]   #The red component at pixel 25,100.

g = n.sample(u=0.5,v=0.5)[1]  #The green component at the central location.

b = n.sample(x=25,v=0.5)[2]  #The blue 25 pixels across, and half way down.


```"""
		pass
	def numpyArray(self, delayed=False, writable=False) -> any: 
		"""Returns the TOP image as a Python NumPy array. Note that since NumPy arrays are referenced by line first, pixels are addressed as [h, w]. Currently data will always be in floating point, regardless of what the texture data format is on the GPU.

* delayed - (Keyword, Optional) If set to True, the download results will be delayed until the next call to numpyArray(), avoiding stalling the GPU waiting for the result immediately. This is useful to avoid long stalls that occur if immediately asking for the result. Each call with return the image that was 'current' on the previous call to numpyArray(). None will be returned if there isn't a result available. You should always check the return value against None to make sure you have a result. Call numpyArray() again, ideally on the next frame or later, to get the result. If you always need a result, you can call numpyArray() a second time in the event None is returned on the first call.

* writable - (Keyword, Optional) If set to True, the memory in the numpy array will be allocated in such a way that writes to it arn't slow. By default the memory the numpy array holds can be allocated in such a way that is very slow to write to. Note that in either case, writing to the numpy array will * not*  change the data in the TOP."""
		pass
	def save(self, filepath, asynchronous=False, createFolders=False, quality=1.0, metadata=[]) -> any: 
		"""Saves the image to the file system. Support file formats are: ```.tif</code>, <code>.tiff</code>, <code>.jpg</code>, <code>.jpeg</code>, <code>.bmp</code>, <code>.png</code>, <code>.exr</code> and <code>.dds```. Returns the filename and path used.

* filepath - (Optional) The path and filename to save to. If not given then a default filename will be used, and the file will be saved in the ```project.folder``` folder.

* aysnchronous - (Keyword, Optional) If True, the save will occur in another thread. The file may not be done writing at the time this function returns.

* createFolders - (Keyword, Optional) If True, folders listed in the path that don't exist will be created.

* quality - (Keyword, Optional) Specify the compression quality used. Values range from 0 (lowest quality, small size) to 1 (best quality, largest size).

* metadata - (Keyword, Optional) A list of string pairs that will be inserted into the file's metadata section. Any type of list structure is supported (dictionary, tuple, etc) as long as each metadata item has two entries (key & value). '''Note:''' Only supported on EXR files.

```python


name = n.save()   #save in default format with default name.

n.save('picture.jpg')

n.save('image.exr', metadata=[ ('my_key', 'my_value'), ('author_name', 'derivative') ] ); # save as .exr with custom metadata


```"""
		pass
	def saveByteArray(self, filetype, quality=1.0, metadata=[]) -> bytearray: 
		"""Saves the image to a bytearray object in the requested file format. Support file formats are: .tif, .tiff, .jpg, .jpeg, .bmp, .png, .exr and .dds. Returns the bytearray object. To get the raw image data use ```numpyArray()</code> or <code>cudaArray()``` instead.

* filetype - (Optional) A string specifying the file type to save as. If not given the default file type '.tiff' will be used. Just the suffix of the string is used to determine the file type. E.g '.tiff', 'file.tiff', 'C:/Files/file.tiff' will all work. '''Suffix must include the period'''.

* quality - (Keyword, Optional) Specify the compression quality used. Values range from 0 (lowest quality, small size) to 1 (best quality, largest size).

* metadata - (Keyword, Optional) A list of string pairs that will be inserted into the file's metadata section. Any type of list structure is supported (dictionary, tuple, etc) as long as each metadata item has two entries (key & value). '''Note:''' Only supported on EXR files.

```python


arr = n.saveByteArray() # save in default format.

arr = n.saveByteArray('.jpg') # save as .jpg

arr = n.saveByteArray('.exr', metadata=[ ('my_key', 'my_value'), ('author_name', 'derivative') ] ); # save as .exr with custom metadata


```"""
		pass
	def cudaMemory(self, ) -> CUDAMemory: 
		"""Copies the contents of the TOP to a newly allocated block of raw CUDA memory. The CUDA memory will be deallocated when the returned [[CUDAMemory_Class|CUDAMemory]] object is deallocated. Ensure you keep a reference to the returned object around as long as you are using it."""
		pass
	pass


class zedTOP(TOP,OP):
	""""""
	par : parameter.zedTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.zedTOP & parameter.TOP & parameter.OP"""
	pass


class webrenderTOP(TOP,OP):
	""""""
	loaded : bool
	"""The loaded state of the current webpage."""
	par : parameter.webrenderTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.webrenderTOP & parameter.TOP & parameter.OP"""
	def interactMouse(self, u, v, leftClick=0, middleClick=0, rightClick=0, left=False, middle=False, right=False, wheel=0, pixels=False) -> None: 
		"""Send mouse clicks, rollovers, moves and drags to the webpage.

* u - The first coordinate for the click to occur at.

* v - The second coordinate for the click to occur at.

* leftClick, middleClick, rightClick -  (Keyword, Optional) Use to specify the number of times a button is clicked on.

* left, middle, right -  (Keyword, Optional) Use to specify if the button is being pressed.  When set to False it simulates a mouse move with the button up.  The first time the button is set to True will initiate a virtual mouse down on the web page at the coordinates u,v.  Subsequent True states will simulate a drag (mouse button down and moving).  Simulate a mouse-up by calling the button set to False, e.g. left=False.

* wheel -  (Keyword, Optional) Roll the mouse wheel

* pixels - (Keyword, Optional) When True, the coordinates are treated as pixel offsets.  When False, they are treated as normalized values.

* aux - (Keyword, Optional) Auxiliary data.

```python


op('webrender1').interactMouse(0.5, 0.5) # roll over the middle of the webpage

op('webrender1').interactMouse(0.5, 0.5, leftClick=2) # double click the middle of the webpage


```"""
		pass
	def executeJavaScript(self, script) -> None: 
		"""Execute a line of javascript on the current webpage.

* script - The line to be executed."""
		pass
	def sendKey(self, char, shift=False, alt=False, ctrl=False, cmd=False) -> None: 
		"""Send key characters to the webpage.

* char - ASCII value or name of a character or key.  Key name matches the names from the [[Keyboard In DAT]].

* shift - (Keyword, Optional) shift key state.

* alt - (Keyword, Optional) alt key state.

* ctrl - (Keyword, Optional) ctrl key state.

* cmd - (Keyword, Optional) cmd key state.

```python


op('webrender1').sendKey(65)      # sends the character 'A'

op('webrender1').sendKey('left')  # sends the left arrow key


```"""
		pass
	def sendString(self, char) -> None: 
		"""Send a string of characters to the webpage.

```python


op('webrender1').sendString('TouchDesigner')  # sends the string TouchDesigner


```"""
		pass
	pass


class viosoTOP(TOP,OP):
	""""""
	par : parameter.viosoTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.viosoTOP & parameter.TOP & parameter.OP"""
	pass


class videostreamoutTOP(TOP,OP):
	""""""
	streamURL : str
	"""The URL to connect to this operator's stream."""
	par : parameter.videostreamoutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.videostreamoutTOP & parameter.TOP & parameter.OP"""
	pass


class videostreaminTOP(TOP,OP):
	""""""
	connectionsFailed : int
	"""The number of times this operator has failed to make a connection to any URL."""
	connectionsLost : int
	"""The number of times this operator has lost a connection it has previous successfully established."""
	frameTime : float
	"""The timestamp of the currently shown frame, in seconds."""
	isConnected : bool
	"""True if connected to target URL."""
	isConnecting : bool
	"""True if attempting to connect to target URL."""
	isOddField : bool
	"""When de-interlacing, this tells if the odd field is currently being shown."""
	videoHeight : int
	"""Height of the movie, in pixels."""
	videoWidth : int
	"""Width of the movie, in pixels."""
	par : parameter.videostreaminTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.videostreaminTOP & parameter.TOP & parameter.OP"""
	def unload(self, cacheMemory=False) -> None: 
		"""Unloads the video stream and frees it's memory usage. The stream will open again next time it cooks, so make sure nothing is still using it to keep it closed.

* cacheMemory - (Keyword, Optional) If True the memory (textures, upload buffers) of the movie will be cached for use by another movie later on. Useful if you are opening/closing many movies with the same codec and resolution."""
		pass
	pass


class videodeviceoutTOP(TOP,OP):
	""""""
	par : parameter.videodeviceoutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.videodeviceoutTOP & parameter.TOP & parameter.OP"""
	pass


class videodeviceinTOP(TOP,OP):
	""""""
	isConnected : bool
	"""True if any device is currently streaming to this operator.."""
	inputSignalFormat : string
	"""If available for the current Library, returns a string for the input signal format. This string can be used to set the 'Signal Format' menu on the Video Device Out TOP."""
	par : parameter.videodeviceinTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.videodeviceinTOP & parameter.TOP & parameter.OP"""
	pass


class underTOP(TOP,OP):
	""""""
	par : parameter.underTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.underTOP & parameter.TOP & parameter.OP"""
	pass


class transformTOP(TOP,OP):
	""""""
	par : parameter.transformTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.transformTOP & parameter.TOP & parameter.OP"""
	pass


class touchoutTOP(TOP,OP):
	""""""
	par : parameter.touchoutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.touchoutTOP & parameter.TOP & parameter.OP"""
	pass


class touchinTOP(TOP,OP):
	""""""
	par : parameter.touchinTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.touchinTOP & parameter.TOP & parameter.OP"""
	pass


class timemachineTOP(TOP,OP):
	""""""
	par : parameter.timemachineTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.timemachineTOP & parameter.TOP & parameter.OP"""
	pass


class tileTOP(TOP,OP):
	""""""
	par : parameter.tileTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.tileTOP & parameter.TOP & parameter.OP"""
	pass


class thresholdTOP(TOP,OP):
	""""""
	par : parameter.thresholdTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.thresholdTOP & parameter.TOP & parameter.OP"""
	pass


class texture3dTOP(TOP,OP):
	""""""
	par : parameter.texture3dTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.texture3dTOP & parameter.TOP & parameter.OP"""
	pass


class textTOP(TOP,OP):
	""""""
	curText : str
	"""Current text contents, when used with a [[Field COMP]]."""
	cursorEnd : int
	"""Get or set cursor end position, when used with a [[Field COMP]]."""
	cursorStart : int
	"""Get or set cursor start position, when used with a [[Field COMP]]."""
	fontDescender : int
	"""The descender of the current font, in pixels. This is the distance from the baseline to the bottom of lowest hanging character in the font. This value does not change based on the currently displayed text."""
	selectedText : str
	"""Selected contents, when used with a [[Field COMP]]."""
	textHeight : int
	"""Calculated height of text, in pixels. This value does '''not''' changes based on the particular of characters in the string. It only depends on the number of lines, line spacing, positioning and font metrics of the font."""
	textWidth : int
	"""Calculated width of text, in pixels. This value '''does''' change depending on the particular characters in the string. Different characters have difference advance widths, and this value is the sum of all the advance widths of the characters."""
	numLines : int
	"""Get the number of lines of the outputted text, after operations such as word-wrap have been applied."""
	ascender : float
	"""The ascender of the font, as described by the font's metrics."""
	descender : float
	"""The descender of the font, as described by the font's metrics."""
	capHeight : float
	"""The cap height of the font, as described by the font's metrics. This is usually the height of a capital H."""
	xHeight : float
	"""The x height of the font, as described by the font's metrics. This is usually the height of a lower case x."""
	lineGap : float
	"""The suggested gap between lines, as described by the font's metrics."""
	par : parameter.textTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.textTOP & parameter.TOP & parameter.OP"""
	def fontSupportsChars(self, str) -> bool: 
		"""Returns True if every character maps to a glyph. This doesn't mean the font supports the language in all cases. Glyphs that come from ligatures etc. may still be missing from the font.

* str - The string to be analyzed."""
		pass
	def evalTextSize(self, str) -> any: 
		"""Evaluates the width and height of the given string using the operators settings.  Does not include the word wrap and auto size font options.

* str - The string to be measured."""
		pass
	def lines(self, ) -> any: 
		"""Returns a list of [[TextLine Class]] objects. This list of lines is formed after operations such as word-wrap have been applied."""
		pass
	pass


class td():
	"""The td module contains all TouchDesigner related Python classes and utilities. All td module members and methods are imported when the application launches and are automatically available in scripts, expressions, and the textport.<br><br>For additional helpful Python classes and utilities not directly related to TouchDesigner, see the [[Tdu Module]]"""
	me : OP
	"""Reference to the current [[OP Class|operator]] that is being executed or evaluated. This can be used in parameter expressions, or DAT scripts."""
	absTime : absTime
	"""Reference to the [[AbsTime Class|AbsTime]] object."""
	app : app
	"""Reference to the [[App Class|application]] installation."""
	ext : ext
	"""Reference to the extension searching object. See [[extensions]] for more information."""
	families : dict
	"""A dictionary containing a list of [[OP Class|operator]] types for each operator family. 

```python


for a in families['SOP']:

	# do something with a


```
"""
	licenses : licenses
	"""Reference to the currently installed [[Licenses Class|licences]]."""
	mod : mod
	"""Reference to the [[MOD Class|Module On Demand]] object."""
	monitors : monitors
	"""Reference to the group of available [[Monitors Class|monitors]]."""
	op : OP
	"""The operator finder object, for accessing operators through paths or shortcuts. '''Note:''' a version of this method that searches relative to a specific operator is also in [[OP Class]].



```op(pattern1, pattern2..., includeUtility=False) &rarr; [[OP Class|OP]] or None```

<blockquote>

Returns the first OP whose path matches the given pattern, relative to ```root```. Will return None if nothing is found. Multiple patterns may be specified which are all added to the search. Numeric OP ids may also be used.

*  ```pattern``` - Can be string following the [[Pattern Matching]] rules, specifying which OP to return, or an integer, which must be an OP Id. Multiple patterns can be given, the first matching OP will be returned.

*  ```includeUtility``` '''(Optional)''' - if True, allow [[Network_Utilities:_Comments,_Network_Boxes,_Annotates|Utility nodes]] to be returned. If False, Utility operators will be ignored.



```python


b = op('project1')

b = op('foot* ', 'hand* ')

b = op(154)


```


</blockquote>

```op.shortcut &rarr; OP```

<blockquote>

:An operator specified with by a [[Global OP Shortcut]]. If no operator exists an exception is raised. These shortcuts are global, and must be unique. That is, cutting and pasting an operator with a Global OP Shortcut specified will lead to a name conflict. One shortcut must be renamed in that case. Furthermore, only components can be given Global OP Shortcuts.

: * ```shortcut``` - Corresponds to the Global OP Shortcut parameter specified in the target operator.

```python


b = op.Videoplayer 


```


To list all Global OP Shortcuts:

```python


for x in op:

	print(x)


```


</blockquote>"""
	parent : OP
	"""The [[Parent Shortcut|Parent Shortcut]] object, for accessing parent components through indices or shortcuts.

    

'''Note:''' a version of this method that searches from a specific operator is also in [[OP Class]].



```parent(n)  OP or None```



The nth parent of the current operator. If n not specified, returns the parent. If n = 2, returns the parent of the parent, etc. If no parent exists at that level, None is returned.

* n - (Optional) n is the number of levels up to climb. When n = 1 it will return the operator's parent.

```python


p = parent(2) #grandfather


```


```parent.shortcut  OP```



A parent component specified with a shortcut. If no parent exists an exception is raised.

* shortcut - Corresponds to the [[Parent Shortcut]] parameter specified in the target parent.

```python


   n = parent.Videoplayer


```


See also Parent Shortcut for more examples."""
	iop : OP
	"""The Internal Operator Shortcut object, for accessing internal shortcuts.

    

'''Note:''' a version of this method that searches from a specific operator is also in [[OP Class]]."""
	ipar : OP
	"""The Internal Operator Parameter Shortcut object, for accessing internal shortcuts.

    

'''Note:''' a version of this method that searches from a specific operator is also in [[OP Class]]."""
	project : project
	"""Reference to the [[Project Class|project session]]."""
	root : OP
	"""Reference to the topmost root [[OP Class|operator]]."""
	runs : runs
	"""Reference to the [[Runs Class|runs]] object, which contains delayed executions."""
	sysinfo : sysinfo
	"""Reference to the [[SysInfo Class|system information]]."""
	ui : ui
	"""Reference to the [[UI Class|ui options]]."""
	par : parameter.td
	"""Parameters of parameter.td"""
	def ops(self, pattern1, pattern2, *args, includeUtility=False) -> list: 
		"""Returns a (possibly empty) list of OPs that match the patterns, relative to this OP.

Multiple patterns may be provided. Numeric OP ids may also be used.

* pattern - Can be string following the [[Pattern Matching]] rules, specifying which OPs to return, or an integer, which must be an OP Id. Multiple patterns can be given and all matched OPs will be returned.

Note a version of this method that searches relative to an operator is also in the [[OP Class]].

```python


newlist = n.ops('arm* ', 'leg* ', 'leg5/foot* ')


```"""
		pass
	def passive(self, OP) -> OP: 
		"""Returns a passive version of the [[OP Class|operator]]. Passive OPs do not cook before their members are accessed."""
		pass
	def run(self, script, arg1, arg2, *args, endFrame=False, fromOP=None, asParameter=False, group=None, delayFrames=0, delayMilliSeconds=0, delayRef=me) -> Run: 
		"""[[Run Class|Run]] the script, returning a [[Run Class|Run]] object which can be used to optionally modify its execution. This is most often used to run a script with a delay, as specified in the delayFrames or delayMilliSeconds arguments. See [[Run Command Examples]] for more info.

* script - A string that is the script code to execute.

* arg - (Optional) One or more arguments to be passed into the script when it executes. They are accessible in the script using a tuple named args.

* endFrame - (Keyword, Optional) If True, the execution will be delayed until the end of the current frame.

* fromOP - (Keyword, Optional) Specifies an optional [[OP Class|operator]] from which the execution will be run relative to.

* asParameter - (Keyword, Optional) When fromOP used, run relative to a parameter of fromOP.

* group - (Keyword, Optional) Can be used to specify a string label for the group of Run objects this belongs to. This label can then be used with the [[Runs Class|td.runs]] object to modify its execution.

* delayFrames - (Keyword, Optional) The number of frames to wait before executing the script.

* delayMilliSeconds - (Keyword, Optional) The number of milliseconds to wait before executing the script. This value is rounded to the nearest frame.

* delayRef - (Keyword, Optional) Specifies an optional [[OP Class|operator]] from which the delay time is derived. You can use your own [[Time COMP|independent time component]] or ```op.TDResources```, a built-in independent time component."""
		pass
	def fetchStamp(self, key, default) -> any: 
		"""Return an object from the global stamped parameters. If the item is not found, the default is returned instead. Parameters can be stamped with the [[Copy SOP]].

* key - The name of the entry to retrieve.

* default - If no item is found then the passed value is returned instead.

```python


v = fetchStamp('sides', 3)


```"""
		pass
	def var(self, varName) -> str: 
		"""Find the value for the given [[Variables|variable]]."""
		pass
	def varExists(self, varName) -> bool: 
		"""Returns true if the [[Variables|variable]] is defined."""
		pass
	def varOwner(self, varName) -> any: 
		"""Returns the [[OP Class|operator]] that defines the [[Variables|variable]], or None if it's not defined."""
		pass
	def isMainThread(self, ) -> bool: 
		"""Is True when called from the main application editing thread. Any calls that access operators, etc., must be called from the main thread."""
		pass
	def clear(self, ) -> None: 
		"""Clear the textport of all text."""
		pass
	pass


class syphonspoutoutTOP(TOP,OP):
	""""""
	par : parameter.syphonspoutoutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.syphonspoutoutTOP & parameter.TOP & parameter.OP"""
	pass


class syphonspoutinTOP(TOP,OP):
	""""""
	par : parameter.syphonspoutinTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.syphonspoutinTOP & parameter.TOP & parameter.OP"""
	pass


class switchTOP(TOP,OP):
	""""""
	par : parameter.switchTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.switchTOP & parameter.TOP & parameter.OP"""
	pass


class svgTOP(TOP,OP):
	""""""
	par : parameter.svgTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.svgTOP & parameter.TOP & parameter.OP"""
	pass


class subtractTOP(TOP,OP):
	""""""
	par : parameter.subtractTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.subtractTOP & parameter.TOP & parameter.OP"""
	pass


class substanceTOP(TOP,OP):
	""""""
	par : parameter.substanceTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.substanceTOP & parameter.TOP & parameter.OP"""
	pass


class substanceselectTOP(TOP,OP):
	""""""
	par : parameter.substanceselectTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.substanceselectTOP & parameter.TOP & parameter.OP"""
	pass


class ssaoTOP(TOP,OP):
	""""""
	par : parameter.ssaoTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.ssaoTOP & parameter.TOP & parameter.OP"""
	pass


class SOP(OP):
	"""A [[SOP]] describes a reference to a SOP operator, containing [[Points Class|points]] and [[Prims Class|primitives]]."""
	compare : bool
	"""Get or set [[Compare Flag]]."""
	template : bool
	"""Get or set [[Template Flag]]."""
	points : td.Points
	"""The set of [[Points Class|points]] contained in this SOP."""
	prims : td.Prims
	"""The set of [[Prims Class|primitives]] contained in this SOP."""
	numPoints : int
	"""The number of [[Points Class|points]] contained in this SOP."""
	numVertices : int
	"""The number of [[Vertex Class|vertices]] contained in all primitives within this SOP."""
	numPrims : int
	"""The number of [[Prims Class|primitivies]] contained in this SOP."""
	pointAttribs : td.Attributes
	"""The set of point [[Attributes Class|attributes]] defined in this SOP."""
	primAttribs : td.Attributes
	"""The set of primitive [[Attributes Class|attributes]] defined in this SOP."""
	vertexAttribs : td.Attributes
	"""The set of vertex [[Attributes Class|attributes]] defined in this SOP."""
	pointGroups : dict
	"""Returns a dictionary of point [[Group Class|groups]] defined for this SOP."""
	primGroups : dict
	"""Returns a dictionary of primitive [[Group Class|groups]] defined for this SOP."""
	center : tdu.Position
	"""Get or set the barycentric coordinate of this operator's geometry. It is expressed as a [[Position Class|Position]]."""
	min : tdu.Position
	"""The minimum coordinates of this operator's geometry along each dimension, expressed as a [[Position Class|Position]]."""
	max : tdu.Position
	"""The maximum coordinates of this operator's geometry along each dimension, expressed as [[Position Class|Position]]."""
	size : tdu.Position
	"""The size of this operator's geometry along each dimension, expressed as a [[Position Class|Position]]."""
	isSOP : bool
	"""True if the operator is a SOP."""
	par : parameter.SOP|parameter.OP
	"""Parameters of parameter.SOP & parameter.OP"""
	def computeBounds(self, ) -> Bounds: 
		"""Returns an object with the bounds, center and size of the SOP's geometry. Keywords can be used to check if the correct render or display flags are set."""
		pass
	def save(self, filepath, createFolders=False) -> any: 
		"""Saves the geometry to the file system. Multiple file types are supported. Returns the filename and path saved.

* filepath - (Optional) The path and filename to save to. If not given then a default filename will be used, and the file will be saved in the project.folder folder.

* createFolders - (Keyword, Optional) If True, it creates the not existent directories provided by the filepath.

```python


name = n.save()   #save in native format with default name.

n.save('output.bgeo')  #alternate format compatible with some other modelling packages.


```"""
		pass
	pass


class zedSOP(SOP,OP):
	""""""
	par : parameter.zedSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.zedSOP & parameter.SOP & parameter.OP"""
	pass


class wireframeSOP(SOP,OP):
	""""""
	par : parameter.wireframeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.wireframeSOP & parameter.SOP & parameter.OP"""
	pass


class vertexSOP(SOP,OP):
	""""""
	inputColor : tuple(r, g, b, a)
	"""The current point or vertex color being evaluated, from the first input, or a default if not present, expressed as a 4-tuple."""
	inputColor2 : tuple(r, g, b, a)
	"""The current point or vertex color being evaluated, from the second input, or a default if not present, expressed as a 4-tuple."""
	inputNormal : tuple(n1, n2, n3)
	"""The current point or vertex normal being evaluated, from the first input, or a default if not present, expressed as a 3-tuple."""
	inputNormal2 : tuple(n1, n2, n3)
	"""The current point or vertex normal being evaluated, from the second input, or a default if not present, expressed as a 3-tuple."""
	inputTexture : tuple(u, v, w)
	"""The current point or vertex texture being evaluated, from the first input, or a default if not present, expressed as a 3-tuple."""
	inputTexture2 : tuple(u, v, w)
	"""The current point or vertex texture being evaluated, from the second input, or a default if not present, expressed as a 3-tuple."""
	inputVertex : Vertex
	"""The current [[Vertex Class|vertex]] being evaluated, from the first input."""
	inputVertex2 : Vertex
	"""The current [[Vertex Class|vertex]] being evaluated, from the second input."""
	par : parameter.vertexSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.vertexSOP & parameter.SOP & parameter.OP"""
	pass


class twistSOP(SOP,OP):
	""""""
	par : parameter.twistSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.twistSOP & parameter.SOP & parameter.OP"""
	pass


class tubeSOP(SOP,OP):
	""""""
	par : parameter.tubeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.tubeSOP & parameter.SOP & parameter.OP"""
	pass


class tristripSOP(SOP,OP):
	""""""
	par : parameter.tristripSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.tristripSOP & parameter.SOP & parameter.OP"""
	pass


class trimSOP(SOP,OP):
	""""""
	par : parameter.trimSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.trimSOP & parameter.SOP & parameter.OP"""
	pass


class transformSOP(SOP,OP):
	""""""
	par : parameter.transformSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.transformSOP & parameter.SOP & parameter.OP"""
	pass


class trailSOP(SOP,OP):
	""""""
	par : parameter.trailSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.trailSOP & parameter.SOP & parameter.OP"""
	pass


class traceSOP(SOP,OP):
	""""""
	par : parameter.traceSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.traceSOP & parameter.SOP & parameter.OP"""
	pass


class torusSOP(SOP,OP):
	""""""
	par : parameter.torusSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.torusSOP & parameter.SOP & parameter.OP"""
	pass


class textureSOP(SOP,OP):
	""""""
	par : parameter.textureSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.textureSOP & parameter.SOP & parameter.OP"""
	pass


class textSOP(SOP,OP):
	""""""
	numLines : int
	"""Get the number of lines of the outputted text, after operations such as word-wrap have been applied."""
	ascender : float
	"""The ascender of the font, as described by the font's metrics."""
	descender : float
	"""The descender of the font, as described by the font's metrics."""
	capHeight : float
	"""The cap height of the font, as described by the font's metrics. This is usually the height of a capital H."""
	xHeight : float
	"""The x height of the font, as described by the font's metrics. This is usually the height of a lower case x."""
	lineGap : float
	"""The suggested gap between lines, as described by the font's metrics."""
	numGlyphs : int
	"""The number of glyphs that were generated. Note that this isn't nessesarily the number of characters (code points) in the original string."""
	par : parameter.textSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.textSOP & parameter.SOP & parameter.OP"""
	def fontSupportsChars(self, str) -> bool: 
		"""Returns True if every character maps to a glyph. This doesn't mean the font supports the language in all cases. Glyphs that come from ligatures etc. may still be missing from the font.

* str - The string to be analyzed."""
		pass
	def lines(self, ) -> any: 
		"""Get the number of lines of the outputted text, after operations such as word-wrap have been applied."""
		pass
	pass


class switchSOP(SOP,OP):
	""""""
	par : parameter.switchSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.switchSOP & parameter.SOP & parameter.OP"""
	pass


class sweepSOP(SOP,OP):
	""""""
	inputVertex : Vertex
	"""The current [[Vertex Class|vertex]] being evaluated, along the backbone input."""
	par : parameter.sweepSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.sweepSOP & parameter.SOP & parameter.OP"""
	pass


class surfsectSOP(SOP,OP):
	""""""
	par : parameter.surfsectSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.surfsectSOP & parameter.SOP & parameter.OP"""
	pass


class superquadSOP(SOP,OP):
	""""""
	par : parameter.superquadSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.superquadSOP & parameter.SOP & parameter.OP"""
	pass


class subdivideSOP(SOP,OP):
	""""""
	par : parameter.subdivideSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.subdivideSOP & parameter.SOP & parameter.OP"""
	pass


class stitchSOP(SOP,OP):
	""""""
	par : parameter.stitchSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.stitchSOP & parameter.SOP & parameter.OP"""
	pass


class spriteSOP(SOP,OP):
	""""""
	par : parameter.spriteSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.spriteSOP & parameter.SOP & parameter.OP"""
	pass


class springSOP(SOP,OP):
	""""""
	par : parameter.springSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.springSOP & parameter.SOP & parameter.OP"""
	pass


class sphereSOP(SOP,OP):
	""""""
	par : parameter.sphereSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.sphereSOP & parameter.SOP & parameter.OP"""
	pass


class sortSOP(SOP,OP):
	""""""
	par : parameter.sortSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.sortSOP & parameter.SOP & parameter.OP"""
	pass


class slopeTOP(TOP,OP):
	""""""
	par : parameter.slopeTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.slopeTOP & parameter.TOP & parameter.OP"""
	pass


class skinSOP(SOP,OP):
	""""""
	par : parameter.skinSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.skinSOP & parameter.SOP & parameter.OP"""
	pass


class sharedmemoutTOP(TOP,OP):
	""""""
	par : parameter.sharedmemoutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.sharedmemoutTOP & parameter.TOP & parameter.OP"""
	pass


class sharedmeminTOP(TOP,OP):
	""""""
	par : parameter.sharedmeminTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.sharedmeminTOP & parameter.TOP & parameter.OP"""
	pass


class sequenceblendSOP(SOP,OP):
	""""""
	par : parameter.sequenceblendSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.sequenceblendSOP & parameter.SOP & parameter.OP"""
	pass


class Sequence():
	"""An object describing a set of sequential parameter blocks. Accessed via the ```sequence</code> member of [[Par Class|parameters]]. You can use any parameter inside the sequence to retreive it's <code>sequence``` object.

```python


seq = op('/base1').par.iopshortcut1.sequence	# get the sequence object

print(len(seq))									# number of par blocks in the sequence

print(seq[0])									# first par block in the sequence

for parBlock in seq:

	print(parBlock)								# print all par blocks



seq.numBlocks += 1							    # add a new block of parameters (same as pressing + in the UI)





# A parameter block is a tuple of parameters that make up one block in a set of sequential parameters.


```
"""
	owner : OP
	"""The OP to which this object belongs."""
	numBlocks : int
	"""Get or set the total number of parameter blocks in this sequence."""
	maxBlocks : int
	"""The maximum number of blocks allowed in the sequence, or None if limitless."""
	blocks : set
	"""The set of all blocks in this sequence. A block is a set of parameters which can be repeated in an operator."""
	par : parameter.Sequence
	"""Parameters of parameter.Sequence"""
	pass


class selectTOP(TOP,OP):
	""""""
	par : parameter.selectTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.selectTOP & parameter.TOP & parameter.OP"""
	pass


class selectSOP(SOP,OP):
	""""""
	par : parameter.selectSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.selectSOP & parameter.SOP & parameter.OP"""
	pass


class scriptSOP(SOP,OP):
	""""""
	par : parameter.scriptSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.scriptSOP & parameter.SOP & parameter.OP"""
	def clear(self, ) -> None: 
		"""Remove all geometry."""
		pass
	def copy(self, sop) -> None: 
		"""Copy geometry from the specified [[SOP]] operator.

* sop - The SOP to copy geometry from. Geometry currently in this SOP will be removed."""
		pass
	def appendPoint(self, ) -> Point: 
		"""Append a [[Point Class|point]] to this SOP. The appended point will be returned."""
		pass
	def appendPoly(self, numVertices, closed=True, addPoints=True) -> Poly: 
		"""Append a [[Poly Class|poly]] to this SOP. Returns the appended polygon. The returned polygon, is a list of vertices, and if ```addPoints=True</code>, then <code>polygon[0].point.x``` can be set to the x value of the first point of the polygon, for example.

* numVertices - Specifies the initial number of [[Vertex Class|vertices]].

* closed - (Keyword, Optional) Specifies whether or not the last [[Vertex Class|vertex]] of the polygon will connect to the first. An open polygon will be drawn as a line.

* addPoints - (Keyword, Optional) If True, a new [[Point Class|point]] will be attached to each [[Vertex Class|vertex]], otherwise the [[Vertex Class|vertex]] point references will need to be manually set afterwards. Manually add them when creating [[Poly Class|polygons]] with shared [[Vertex Class|vertices]]."""
		pass
	def appendBezier(self, numVertices, closed=False, order=4, addPoints=True) -> Bezier: 
		"""Append a [[Bezier Class|Bezier]] to this SOP. Returns the appended Bezier.

*  numVertices - Specifies the initial number of [[Vertex Class|vertices]].  The number of [[Vertex Class|vertices]] '''must''' correspond to the order (degree-1) and closed/open state of the curve.  For closed curves, the number of vertices must be a multiple of the degree.  For open curves, it must be one more than a multiple of the degree.

```python


scriptOp.appendBezier(6, closed=True) #closed, cubic, 6 vertices, or 2 spans


```


```python


scriptOp.appendBezier(7) #open, cubic, 7 vertices, or 2 spans


```


*  closed - (Keyword, Optional) Specifies whether or not the last [[Vertex Class|vertex]] of the curve will connect to the first. An open Bezier will be drawn as a line.

*  order - (Keyword, Optional) Specifies the degree of the Bezier. By default it creates cubic (order=4) Beziers.

*  addPoints - (Keyword, Optional) If True, a new [[Point Class|point]] will be attached to each [[Vertex Class|vertex]], otherwise the [[Vertex Class|vertex]] point references will need to be manually set afterwards. Use this option when creating Beziers with shared vertices."""
		pass
	def appendMesh(self, numRows, numCols, closedU=False, closedV=False, addPoints=True) -> Mesh: 
		"""Append a [[Mesh Class|mesh]] to this SOP. Returns the appended mesh.

* numRows, numCols - Specifies the initial number of rows and columns.

* closedU - (Keyword, Optional) Specifies whether or not the grid is wrapped in the u direction.

* closedV - (Keyword, Optional) Specifies whether or not the grid is wrapped in the v direction.

* addPoints - (Keyword, Optional) If True, a new [[Point Class|point]] will be attached to each [[Vertex Class|vertex]], otherwise the [[Vertex Class|vertex]] point references will need to be manually set afterwards. Use this option when creating [[Mesh Class|meshes]] with shared [[Vertex Class|vertices]]."""
		pass
	def createPointGroup(self, str) -> any: 
		"""Creates a point [[Group Class|group]] with input string name. Returns an error if the group already exists."""
		pass
	def createPrimGroup(self, str) -> any: 
		"""Creates a primitive [[Group Class|group]] with input string name. Returns an error if the group already exists."""
		pass
	def appendCustomPage(self, name) -> Page: 
		"""Add a new [[Page Class|page]] of custom parameters. See [[Page Class]] for more details.

```python


page = scriptOp.appendCustomPage('Custom1')

page.appendFloat('X1')


```"""
		pass
	def destroyCustomPars(self, ) -> any: 
		"""Remove all custom parameters from COMP."""
		pass
	def sortCustomPages(self, page1, page2, page3, *args) -> None: 
		"""Reorder custom parameter pages.

```python


scriptOp.sortCustomPages('Definition','Controls')


```"""
		pass
	pass


class screenTOP(TOP,OP):
	""""""
	par : parameter.screenTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.screenTOP & parameter.TOP & parameter.OP"""
	pass


class screengrabTOP(TOP,OP):
	""""""
	par : parameter.screengrabTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.screengrabTOP & parameter.TOP & parameter.OP"""
	pass


class scalabledisplayTOP(TOP,OP):
	""""""
	cameraTransform : tdu.Matrix
	"""Gets the loaded camera transform [[Matrix Class|matrix]] for the configuration. This should be referenced in the 'Xform Matrix/CHOP/DAT' parameter of the [[Camera COMP]]."""
	projection : tdu.Matrix
	"""Gets the loaded projection [[Matrix Class|matrix]] for the configuration. This should be referenced in the 'Proj Matrix/CHOP/DAT' parameter of the [[Camera COMP]], with the 'Projection' set to 'Custom Projection Matrix'."""
	par : parameter.scalabledisplayTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.scalabledisplayTOP & parameter.TOP & parameter.OP"""
	pass


class Run():
	"""The Run class describes a single instance of a delayed script execution. See [[Run Command Examples]] for more info.

They can be accessed from the [[Runs Class|runs]] object. Scripts can be executed with delays with the following methods:

```python


DAT.run()

Cell.run()

td.run()


```
"""
	active : bool
	"""Get or set whether or not this script will execute once its target frame is reached."""
	group : string
	"""Get or set the group label associated with this script."""
	isCell : bool
	"""Returns true when the source is a [[Cell Class|cell]], from a Cell.run() call."""
	isDAT : bool
	"""Returns true when the source is a [[DAT Class|DAT]], from a DAT.run() call."""
	isString : bool
	"""Returns true when the source is a string, from a td module run() call"""
	path : OP
	"""The [[OP Class|operator]] location from which this script will execute."""
	remainingFrames : int
	"""Get or set the remaining number of frames before the execution will occur."""
	remainingMilliseconds : int
	"""Get or set the remaining number of milliseconds before the execution will occur."""
	source : [DAT, cell, string]
	"""The source of the run. It will be either a [[DAT Class|DAT]], [[Cell Class|cell]], or string."""
	par : parameter.Run
	"""Parameters of parameter.Run"""
	def kill(self, ) -> None: 
		"""Kill this run before it executes, and remove it from the global runs list, located in the [[td Module]]."""
		pass
	pass


class rgbtohsvTOP(TOP,OP):
	""""""
	par : parameter.rgbtohsvTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.rgbtohsvTOP & parameter.TOP & parameter.OP"""
	pass


class rgbkeyTOP(TOP,OP):
	""""""
	par : parameter.rgbkeyTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.rgbkeyTOP & parameter.TOP & parameter.OP"""
	pass


class revolveSOP(SOP,OP):
	""""""
	par : parameter.revolveSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.revolveSOP & parameter.SOP & parameter.OP"""
	pass


class resolutionTOP(TOP,OP):
	""""""
	par : parameter.resolutionTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.resolutionTOP & parameter.TOP & parameter.OP"""
	pass


class resampleSOP(SOP,OP):
	""""""
	par : parameter.resampleSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.resampleSOP & parameter.SOP & parameter.OP"""
	pass


class reorderTOP(TOP,OP):
	""""""
	par : parameter.reorderTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.reorderTOP & parameter.TOP & parameter.OP"""
	pass


class renderTOP(TOP,OP):
	""""""
	par : parameter.renderTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.renderTOP & parameter.TOP & parameter.OP"""
	pass


class renderselectTOP(TOP,OP):
	""""""
	par : parameter.renderselectTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.renderselectTOP & parameter.TOP & parameter.OP"""
	pass


class renderpassTOP(TOP,OP):
	""""""
	par : parameter.renderpassTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.renderpassTOP & parameter.TOP & parameter.OP"""
	pass


class remapTOP(TOP,OP):
	""""""
	par : parameter.remapTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.remapTOP & parameter.TOP & parameter.OP"""
	pass


class refineSOP(SOP,OP):
	""""""
	par : parameter.refineSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.refineSOP & parameter.SOP & parameter.OP"""
	pass


class rectangleTOP(TOP,OP):
	""""""
	par : parameter.rectangleTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.rectangleTOP & parameter.TOP & parameter.OP"""
	pass


class rectangleSOP(SOP,OP):
	""""""
	par : parameter.rectangleSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.rectangleSOP & parameter.SOP & parameter.OP"""
	pass


class realsenseTOP(TOP,OP):
	""""""
	par : parameter.realsenseTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.realsenseTOP & parameter.TOP & parameter.OP"""
	pass


class raySOP(SOP,OP):
	""""""
	par : parameter.raySOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.raySOP & parameter.SOP & parameter.OP"""
	pass


class rampTOP(TOP,OP):
	""""""
	par : parameter.rampTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.rampTOP & parameter.TOP & parameter.OP"""
	pass


class railsSOP(SOP,OP):
	""""""
	par : parameter.railsSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.railsSOP & parameter.SOP & parameter.OP"""
	pass


class projectSOP(SOP,OP):
	""""""
	par : parameter.projectSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.projectSOP & parameter.SOP & parameter.OP"""
	pass


class projectionTOP(TOP,OP):
	""""""
	par : parameter.projectionTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.projectionTOP & parameter.TOP & parameter.OP"""
	pass


class Project():
	"""The Project class describes the current session.  It can be accessed with the project object, found in the automatically imported [[td Module|td module]]. Members changed in this such as the 'paths' member will be written to disk when the project is saved."""
	folder : str
	"""The folder at which the project resides."""
	name : str
	"""The filename under which the project is saved."""
	saveVersion : str
	"""The [[App Class|App]] version number when the project was last saved."""
	saveBuild : str
	"""The [[App Class|App]] build number when the project was last saved."""
	saveTime : str
	"""The time and date the project was last saved."""
	saveOsName : str
	"""The [[App Class|App]] operating system name when the project was last saved."""
	saveOsVersion : str
	"""The [[App Class|App]] operating system version when the project was last saved."""
	saveOSName : str
	"""The [[App Class|App]] operating system name when the project was last saved."""
	saveOSVersion : str
	"""The [[App Class|App]] operating system version when the project was last saved."""
	paths : dict
	"""A dictionary which can be used to define URL-syntax path prefixes, enabling you to move your media to different locations easily. This dictionary is saved and loaded in the ```.toe</code> file.  Example: Run <code>project.paths['movies'] = 'C:/MyMovies'</code>, and reference it with a parameter expression: <code>movies://butterfly.jpg</code>. To manually convert between expanded and collapsed paths, use <code>tdu.collapsePath()</code> and <code>tdu.expandPath</code> from the [[Tdu Module]], for example <code>tdu.expandPath('movies://butterfly.jpg')</code> expands to <code>C:/MyMovies/butterfly.jpg</code>. If you already have your paths setup, choosing files from file browsers in OPs will create paths using these shortcuts rather than full paths. Additionally, to enable you to have different media locations on different machines, you can put a JSON file in the same folder as your <code>.toe</code> that gets read on startup. This will override any existing locations saved in projects.paths to the new machine specific file paths specified in the .json. Only existing entries in <code>project.paths</code> will be used. If the .json contains path names not specified in <code>project.paths</code>, those will be ignored. It would contain something like <code>{ 'project.paths': { 'movies': 'M:/MyMovies' } }</code>. If your <code>.toe</code> file is called <code>MyProject.10.toe</code>, the JSON file must be called <code>MyProject.Settings.json```. The idea is that this .json would be unique to machines, and not commited to version control or shared between machines."""
	cookRate : float
	"""Get or set the maximum number of frames processed each second. In general you should not need to use this. It is preferred to look at the FPS of the root component to know the cooking rate. Individual [[COMP Class|components]] may have their own rates, specified by rate.

```python


a = project.cookRate # get the current cook rate 

project.cookRate = 30 # set the cook rate to 30 FPS


```


Note: This is displayed and set in the user interface at the bottom-left: the 'FPS' field."""
	realTime : bool
	"""Get or set the real time cooking state. When True, frames may be skipped in order to maintain the cookRate. When False, all frames are processed sequentially regardless of duration. This is useful to render movies out using the Movie File Out TOP without dropping any frames for example.

```python


a = project.realTime

project.realTime = False # turn off real time playback.


```
"""
	isPrivate : bool
	"""True when the project networks cannot be directly viewed."""
	isPrivateKey : bool
	"""True when the private networks are accessible by a pass phrase."""
	cacheParameters : bool
	"""Cache parameter values instead of always evaluating."""
	externalToxModifiedInProject : bool
	"""Callback for when an external tox has been modified in the current project and there are other instances of the same tox loaded elsewhere in the project."""
	externalToxModifiedOnDisk : bool
	"""Callback for when an external tox file has been modified on disk."""
	windowOnTop : bool
	"""Get or set the window on top state."""
	windowStartMode : WindowStartMode
	"""Get or set the window start mode.

The mode is one of: ```WindowStartMode.AUTO</code>, <code>WindowStartMode.FULL</code>, <code>WindowStartMode.LEFT</code>, <code>WindowStartMode.RIGHT</code> or <code>WindowStartMode.CUSTOM```."""
	windowDraw : bool
	"""Get or set the window drawing state."""
	windowStartCustomWidth : int
	"""Get or set the window start width. Only used when windowStartMode is ```WindowStartMode.CUSTOM```."""
	windowStartCustomHeight : int
	"""Get or set the window start height. Only used when windowStartMode is ```WindowStartMode.CUSTOM```."""
	windowStartCustomX : int
	"""Get or set the window start X position. Only used when windowStartMode is ```WindowStartMode.CUSTOM```."""
	windowStartCustomY : int
	"""Get or set the window start Y position. Only used when windowStartMode is ```WindowStartMode.CUSTOM```."""
	performOnStart : bool
	"""Get or set the perform on start state."""
	performWindowPath : OP
	"""Get or set the perform window path."""
	resetAudioOnDeviceChange : bool
	"""Get or set whether audio devices momentarily reset when devices are added or removed to the system."""
	par : parameter.Project
	"""Parameters of parameter.Project"""
	def load(self, path) -> None: 
		"""Load a specific .toe file from disk.

* path - (Optional) The path of the file to load.  If not specified, loads the default[[.toe file]], as specified in preferences.

```python


project.load('test_demo.toe')


```"""
		pass
	def save(self, path, saveExternalToxs=False) -> bool: 
		"""Save the current session to disk.  Returns True if a file was saved, False otherwise (eg, if the file exists, and when prompted, the user selects to not overwrite).

* path - (Optional) If not provided the default/current filename is incremented and used. The current file is project.name under folder project.folder.

* saveExternalToxs - (Keyword, Optional) If set to True, will save out the contents of any COMP that references an external .tox into the referenced .tox file.

```python


project.save('test_demo.toe')

project.save()


```"""
		pass
	def quit(self, force=False, crash=False) -> None: 
		"""Quit the project.

* force - (Keyword, Optional) If set to True, unsaved changes will be discarded without prompting.

* crash - (Keyword, Optional) If set to True, the application will terminate unexpectedly. This is used for system testing.

```python


project.quit()  #quit project, possibly prompting for unsaved changes if 'Prompt to Save on Exit' in Preferences dialog is enabled.

project.quit(force=True)  #quit project immediately.


```"""
		pass
	def addPrivacy(self, key) -> bool: 
		"""Add privacy to a toe file with the given key.

Privacy can only be added to toes that currently have no privacy, and are using a Pro license.

* key - The key phrase. This should resolve to a non-blank string.

```python


project.addPrivacy('secret')


```"""
		pass
	def removePrivacy(self, key) -> bool: 
		"""Completely remove privacy from a toe file.

* key - The current privacy key phrase.

```python


project.removePrivacy('secret')


```"""
		pass
	def accessPrivateContents(self, key) -> bool: 
		"""Gain access to a private file. The file will still be private the next time it is saved or re-opened.

* key - The current privacy key phrase.

```python


project.accessPrivateContents('secret')


```"""
		pass
	def applyWindowSettings(self, ) -> None: 
		"""Applies the project's window start settings to the current TouchDesigner window."""
		pass
	def stack(self, ) -> str: 
		"""Formatted contents of current cook and parameter evaluation stack.

```python


print(project.stack())


```"""
		pass
	def pythonStack(self, ) -> str: 
		"""Formatted contents of current python stack.

```python


print(project.pythonStack())


```"""
		pass
	pass


class profileSOP(SOP,OP):
	""""""
	par : parameter.profileSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.profileSOP & parameter.SOP & parameter.OP"""
	pass


class Prims():
	"""The Prims class describes the set of [[Prim Class|prim objects]] (primitives) owned by one [[SOP Class|SOP]]."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	par : parameter.Prims
	"""Parameters of parameter.Prims"""
	def len(self, Prims) -> int: 
		"""Returns the total number of prims.

```python


a = len(op('box1').prims)


```"""
		pass
	def [index] -> any: 
		"""Get a specific prim given an integer index.

```python


n = op('box1').prims[0]


```"""
		pass
	def Iterator -> any: 
		"""Iterate over each prim.

```python


for m in op('box1').prims:

        # do something with m, which is a Prim


```"""
		pass
	pass


class Prim():
	"""A Prim describes an instance to a single [[Primitive|geometry primitive]].  They are accessible through the [[SOP Class|SOP.prims]] member."""
	center : tdu.Position
	"""Get or set the barycentric coordinate of this primitive. It is expressed as a tdu.Position object."""
	index : int
	"""The primitive index in the list."""
	normal : tdu.Vector
	"""The calculated normal vector of this primitive, expressed as a tdu.Vector object."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	weight : float
	"""The associated weight of the primitive. Only certain primitives, such as those created by the [[Metaball SOP]] can modify this value from its default of 2.0."""
	direction : tdu.Vector
	"""A normalized vector pointing from the centroid of the SOP to the centroid of this primitive."""
	min : tdu.Position
	"""The minimum coordinates of this primitive along each dimension, expressed as a tdu.Position object."""
	max : tdu.Position
	"""The maximum coordinates of this primitive along each dimension, expressed as a tdu.Position object."""
	size : tdu.Position
	"""The size of this primitive along each dimension, expressed as a tdu.Position object."""
	par : parameter.Prim
	"""Parameters of parameter.Prim"""
	def destroy(self, destroyPoints=True) -> None: 
		"""Destroy and remove the actual primitive this object refers to. This operation is only valid when the primitive belongs to a [[scriptSOP Class|scriptSOP]]. Note: after this call, other existing Prim objects in this SOP may no longer be valid.

* destroyPoints - (Keyword, Optional) If True, its [[Point Class|points]] are destroyed as well, if false, they are simply detached. The argument is True by default."""
		pass
	def eval(self, u, v) -> any: 
		"""Evaluate the [[Position Class|position]] on the primitive given the u,v coordinates. u,v should be in the range [0,1]. '''Note:''' Polygons and curves ignore the v parameter.

```python


center = op('box1').prim[0].eval(0.5, 0.5)


```"""
		pass
	def len(self, Prim) -> int: 
		"""Returns the total number of vertices.

```python


a = len(op('box1').prim[0])


```"""
		pass
	def [index] -> any: 
		"""Get specific vertex given an integer index

```python


n = op('box1').prims[5][0]


```"""
		pass
	def [row, col] -> any: 
		"""Get specific vertex from a Mesh given integer row and column values.

```python


v = op('grid1').prims[2,3]


```"""
		pass
	def Iterator -> any: 
		"""Iterate over each vertex.

```python


for m in op('box1').prims[5]:

        # do something with m, which is a Vertex


```"""
		pass
	pass


class primitiveSOP(SOP,OP):
	""""""
	inputColor : tuple(r, g, b, a)
	"""The current primitive color being evaluated or a default if not present, expressed as a 4-tuple."""
	inputPrim : Prim
	"""The current [[Prim Class|primitive]] being evaluated."""
	par : parameter.primitiveSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.primitiveSOP & parameter.SOP & parameter.OP"""
	pass


class prefiltermapTOP(TOP,OP):
	""""""
	par : parameter.prefiltermapTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.prefiltermapTOP & parameter.TOP & parameter.OP"""
	pass


class polystitchSOP(SOP,OP):
	""""""
	par : parameter.polystitchSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.polystitchSOP & parameter.SOP & parameter.OP"""
	pass


class polysplineSOP(SOP,OP):
	""""""
	par : parameter.polysplineSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.polysplineSOP & parameter.SOP & parameter.OP"""
	pass


class polyreduceSOP(SOP,OP):
	""""""
	par : parameter.polyreduceSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.polyreduceSOP & parameter.SOP & parameter.OP"""
	pass


class polypatchSOP(SOP,OP):
	""""""
	par : parameter.polypatchSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.polypatchSOP & parameter.SOP & parameter.OP"""
	pass


class polyloftSOP(SOP,OP):
	""""""
	par : parameter.polyloftSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.polyloftSOP & parameter.SOP & parameter.OP"""
	pass


class Points():
	"""The Points class describes the set of [[Point Class|point objects]] owned by one [[SOP Class|SOP]]."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	par : parameter.Points
	"""Parameters of parameter.Points"""
	def len(self, Points) -> int: 
		"""Returns the total number of points.

```python


a = len(op('box1').points)


```"""
		pass
	def [index] -> any: 
		"""Get a specific point given an integer index.

```python


n = op('box1').points[0]


```"""
		pass
	def Iterator -> any: 
		"""Iterate over each point.

```python


for m in op('box1').points:

        # do something with m, which is a Point


```"""
		pass
	pass


class Point():
	"""A Point describes an instance to a single [[Point|geometry point]].  They are accessible through the [[SOP Class|SOP.points]] member."""
	index : int
	"""The point index in the list."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	P : td.AttributeData
	"""The coordinates as [[AttributeData Class|AttributeData]]. Individual components can be read or written with the [] operator.

```python


point.P[0] = 5

point.P = (1,0,1)


```
"""
	x : float
	"""Get or set x coordinate value. This is the same as P[0]."""
	y : float
	"""Get or set y coordinate value. This is the same as P[1]."""
	z : float
	"""Get or set z coordinate value. This is the same as P[2]."""
	normP : tdu.Position
	"""The normalized position of this point within the bounding box of the SOP. Will always be in the range [0,1]. Expressed as tdu.Position object."""
	par : parameter.Point
	"""Parameters of parameter.Point"""
	def destroy(self, ) -> None: 
		"""Destroy and remove the actual point this object refers to. This operation is only valid when the primitive belongs to a [[scriptSOP Class|scriptSOP]]. Note: after this call, other existing Point objects in this SOP may no longer be valid."""
		pass
	pass


class pointSOP(SOP,OP):
	""""""
	inputColor : tuple(r, g, b, a)
	"""The current point color being evaluated, from the first input, or a default if not present, expressed as a 4-tuple."""
	inputColor2 : tuple(r, g, b, a)
	"""The current point color being evaluated, from the second input, or a default if not present, expressed as a 4-tuple."""
	inputNormal : tuple(n1, n2, n3)
	"""The current point normal being evaluated, from the first input, or a default if not present, expressed as a 3-tuple."""
	inputNormal2 : tuple(n1, n2, n3)
	"""The current point normal being evaluated, from the second input, or a default if not present, expressed as a 3-tuple."""
	inputPoint : Point
	"""The current [[Point Class|point]] being evaluated, from the first input."""
	inputPoint2 : Point
	"""The current [[Point Class|point]] being evaluated, from the second input."""
	inputTexture : tuple(u, v, w)
	"""The current point texture being evaluated, from the first input, or a default if not present, expressed as a 3-tuple."""
	inputTexture2 : tuple(u, v, w)
	"""The current point texture being evaluated, from the second input, or a default if not present, expressed as a 3-tuple."""
	par : parameter.pointSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.pointSOP & parameter.SOP & parameter.OP"""
	pass


class photoshopinTOP(TOP,OP):
	""""""
	isConnected : bool
	"""Is true if the operator is connected to a running instance of Photoshop."""
	isReceivingUpdates : bool
	"""Is true if the operator is receiving image update. It will get updates when it's not locked to a particular document, or if it is locked and the document is opened in that Photoshop instance."""
	par : parameter.photoshopinTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.photoshopinTOP & parameter.TOP & parameter.OP"""
	pass


class Peer():
	"""A Peer describes the network connection originating a message in the callback functions found in [[oscinDAT Class|oscinDAT]], [[tcpipDAT Class|tcpipDAT]], [[udpinDAT Class|udpinDAT]], [[udtinDAT Class|udtinDAT]]."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	port : int
	"""The network port associated with the peer."""
	address : str
	"""The network address associated with the peer."""
	hostname : str
	"""The network hostname associated with the peer."""
	par : parameter.Peer
	"""Parameters of parameter.Peer"""
	def close(self, ) -> bool: 
		"""Close the peer connection. Returns True if successful. Closing a peer can be useful when implementing HTML server protocols for example."""
		pass
	pass


class particleSOP(SOP,OP):
	""""""
	par : parameter.particleSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.particleSOP & parameter.SOP & parameter.OP"""
	def createParticles(self, num) -> any: 
		"""Creates a number of particles without advancing the particle simulation. Returns a list of points, where each point describes a particle. Point attributes (v, life, N, etc.) can be used to modify these or any existing particles.

*  num - The number of particles to create.'"""
		pass
	pass


class ParGroupCollection():
	"""The ParGroupCollection class can be used to access parameter tuples. To access a parameter you need to use its internal name. See also [[Par Class]]."""
	owner : OP
	"""The OP to which this object belongs."""
	par : parameter.ParGroupCollection
	"""Parameters of parameter.ParGroupCollection"""
	pass


class ParCollection():
	"""The ParCollection class can be used to access [[Par Class|Parameters]]. To access a parameter you need to use its internal name, which you can obtain by hovering your mouse over the parameter name, and looking at the popup that will come up. See also [[Par Class]]. An operator's instance of this can be found in ```OP.par```."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	par : parameter.ParCollection
	"""Parameters of parameter.ParCollection"""
	def [name] -> Par: 
		"""[[Par Class|Parameters]] may be easily accessed using the [] subscript and assignment operators.

* name - Must be an exact string name. Wildcards are not supported. If not found None is returned.

```python


p = op('base1').par['Myfloat5']


```"""
		pass
	pass


class Par():
	"""The Par class describes an instance of a single [[Parameter]]. See also [[Custom Parameters]]."""
	valid : bool
	"""True if the referenced parameter currently exists, False if it has been deleted."""
	val : value
	"""Get or set the constant value of the parameter only. To get the parameter's current value, regardless of the [[Parameter Mode]] (constant, expression, export or bound), use the <syntaxhighlight lang=python inline>eval()</syntaxhighlight> method described below.

```python


op('geo1').par.tx.val   # the constant value 

op('geo1').par.tx.eval()   # the evaluated parameter

op('geo1').par.tx.val = 5

op('geo1').par.tx = 5  # equivalent to above, more concise form

op('parexec1').par.op = [parent(), parent(2)] # you can assign a list of ops to a parameter that allows multiple operators


```


When setting this member, the parameter will also be placed in constant mode.  See mode member below.

To set a menu value by its index, use the ```menuIndex``` member as described below."""
	expr : str
	"""Get or set the non-evaluated expression only. To get the parameter's current value, regardless of the [[Parameter Mode]] (constant, expression, export or bound), use the <syntaxhighlight lang=python inline>eval()</syntaxhighlight> method described below.

```python


op('geo1').par.tx.expr = 'absTime.frame'  #set to match current frame


```


When setting this member, the parameter will also be placed in expression mode. See mode member below.

'''NOTE:''' For convenience, the expression is placed in double-quotes so you can safely put in expressions containing single quotes. 'a' and 'a' have the same effect of enclosing strings in python."""
	enableExpr : str
	"""Get or set an expression that controls the enable state for this parameter.

```python


p.enableExpr = 'me.par.X.menuIndex == 5'

# Note the outside quotes, as this is an expression, not an object.


```
"""
	exportOP : OP or None
	"""The [[OP Class|operator]] exporting to this parameter."""
	exportSource : Cell Channel or None
	"""The object exporting to this parameter. Examples: [[Cell Class|Cell]], [[Channel Class|Channel]] or None."""
	bindExpr : expression
	"""Get or set an expression that returns a Parameter object. This can be used to bind this parameter's constant value to the referenced parameter.

```python
p.bindExpr = 'op('geo1').par.tx'
```
  

Note the outside quotes, as bindExpr is an expression, not an object."""
	bindMaster : OP or None
	"""The object to which this parameter is bound to, possibly None."""
	bindReferences : list
	"""The (possibly empty) list of objects which bind to this parameter."""
	bindRange : bool
	"""Get or set parameter's range binding state. If True, min, max, clampMin, clampMax, normMin, normMax, normVal values will be based on master bind parameter. Can only be set on Custom Parameters."""
	hidden : bool
	"""Get the parameter's hidden status. When True the parameter is considered obsolete or irrelevant and should not be modified. They are not shown in the dialog but only maintained for backward compatibility."""
	index : int
	"""A unique identifier for the parameter.  May change in the case of custom parameters."""
	vecIndex : int
	"""The parameter's vector index. For example, <syntaxhighlight lang=python inline>op('geo1').par.tz</syntaxhighlight> would have a value of 2."""
	name : str
	"""Get or set the parameter's unique name.

```python


op('myOperator').par.Custompar.name = 'Translate' 


```


Can only be set on [[Custom Parameters]]."""
	label : str
	"""Get or set the parameter's label.

```python


op('myOperator').par.Custompar.label = 'Translate' 


```


Can only be set on [[Custom Parameters]]."""
	subLabel : str
	"""Returns the name of the sub-label."""
	startSection : bool
	"""Get or set the parameter's separator status. When ```True``` a visible separator is drawn between this parameter and the ones preceding it. Can only be set on [[Custom Parameters]]."""
	displayOnly : bool
	"""Get or set the parameter's displayOnly state. Can only be set on Custom Parameters."""
	readOnly : bool
	"""Get or set the parameter's read only status. When ```True``` the parameter cannot be modified through the UI, only scripting."""
	help : str
	"""Get or set a custom parameter's help text. To see any parameter's help, rollover the parameter while holding the Alt key. For built-in parameters this can be used to get the parameter's help text."""
	tuplet : tuplet
	"""The tuplet of parameters this parameter belongs to. A tuplet is typically a set of parameters sharing one line on a parameter dialog, example: Translate (x, y, z)."""
	tupletName : str
	"""The tuplet name of a parameter.  Example: The tuplet name of a (tx,ty,tz) translate parameter is t."""
	parGroup : tuplet
	"""The [[ParGroup]] of parameters this parameter belongs to. A ParGroup is a set of parameters sharing one line on a parameter dialog with a common label, example: Translate (x, y, z).."""
	min : value
	"""Get or set the parameter's numerical minimum value. The parameter's value will be clamped at that minimum if clampMin = True. Can only be set on [[Custom Parameters]]."""
	max : value
	"""Get or set the parameter's numerical maximum value. The parameter's value will be clamped at that maximum if clampMax = True. Can only be set on [[Custom Parameters]]."""
	clampMin : bool
	"""Get or set the parameter's numerical clamping behavior. If set to clampMin = True, the parameter will clamp on the lower end at the value specified in min Can only be set on [[Custom Parameters]]."""
	clampMax : bool
	"""Get or set the parameter's numerical clamping behavior. If set to clampMax = True, the parameter will clamp on the upper end at the value specified in max Can only be set on [[Custom Parameters]]."""
	default : value
	"""Get or set the parameter's default value. Can only be set on [[Custom Parameters]].  Only one of default, defaultExpr can be set."""
	defaultExpr : str
	"""Get or set the parameter's default expression. Can only be set on [[Custom Parameters]].  Only one of default, defaultExpr can be set.

```python


# value defaults to this expression.

op('base1').par.Size.defaultExpr = 'me.time.frame'


```
"""
	normMin : float
	"""Get or set the parameter's minimum slider value if the parameter is a numerical slider. Can only be set on [[Custom Parameters]]."""
	normMax : float
	"""Get or set the parameter's maximum slider value if the parameter is a numerical slider. Can only be set on [[Custom Parameters]]."""
	normVal : float
	"""Get or set the parameter's value as a normalized slider position. Can only be set on [[Custom Parameters]]."""
	enable : bool
	"""Get or set the parameter's enable state. Can only be set on [[Custom Parameters]]."""
	order : int
	"""Get or set the parameter's position on the parameter page.  Can only be set on [[Custom Parameters]]."""
	page : td.Page
	"""Get or set the parameter page the custom parameter is part of. Can only be set on [[Custom Parameters]]."""
	password : bool
	"""Get or set the parameter's password mode. When True all text is rendered as asterisks. Can only be set on Custom string, int or float parameters. [[Custom Parameters]]."""
	mode : ParMode
	"""Get or set the parameter's evaluation mode.

```python


op('geo1').par.tx.mode = ParMode.EXPRESSION


```


The mode is one of:  ```ParMode.CONSTANT</code>, <code>ParMode.EXPRESSION</code>, or <code>ParMode.EXPORT</code>, or <code>ParMode.BIND```.

See [[Parameter_Dialog#Working_with_Parameter_Modes]] for more information."""
	prevMode : ParMode
	"""The parameter's previous evaluation mode."""
	menuNames : list
	"""Get or set a list of all possible menu choice names. In the case of non menu parameters, None is returned. Can only be set on [[Custom Parameters]]."""
	menuLabels : list
	"""Get or set a list of all possible menu choice labels. In the case of non menu parameters, None is returned. Can only be set on [[Custom Parameters]]."""
	menuIndex : int
	"""Get or set a menu constant value by its index."""
	menuSource : str
	"""Get or set an expression that returns an object with .menuItems .menuNames members.  This can be used to create a custom menu whose entries dynamically follow that of another menu for example. Simple menu sources include another parameter with a menu c, an object created by [[Tdu Module|tdu.TableMenu]], or an object created by [[TDFunctions|TDFunctions.parMenu]].

```python


p.menuSource = 'op('audiodevin1').par.device'


```


Note the outside quotes, as menuSource is an expression, not an object."""
	collapser : bool
	"""Returns True if the parameter is a parent of collapsable parameters (ie. a collapser)."""
	collapsable : bool
	"""Returns True if the parameter is collapsable."""
	sequence : set
	"""The set of [[Sequence Class|sequential]] parameter blocks this parameter belongs to, or None."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	styleCloneImmune : bool
	"""Get or set the parameter's style clone immunity. When ```False</code>, the parameter definition is matched to any matching master parameter its operator is cloned to. When <code>True```, it is left unchanged."""
	lastScriptChange : tuple
	"""Return information about when this parameter was last modified by a script. Cleared when the parameter is updated via the UI.

```python


python >>> op('/level1').par.invert.lastScriptChange

SetInfo(dat=type:textDAT path:/text1, function='<module>', line=1, frame=300061, timeStamp=1613150878)


```
"""
	isDefault : bool
	"""True when the parameter value, expression and mode are in their default settings."""
	isCustom : bool
	"""True for [[Custom Parameters]]."""
	isPulse : bool
	"""True for pulse parameters."""
	isMomentary : bool
	"""True for momentary parameters."""
	isMenu : bool
	"""True for menu parameters."""
	isNumber : bool
	"""True for numeric parameters."""
	isFloat : bool
	"""True for floating point numeric parameters."""
	isInt : bool
	"""True for integer numeric parameters."""
	isOP : bool
	"""True for OP parameters."""
	isPython : bool
	"""True for python parameters."""
	isString : bool
	"""True for string parameters."""
	isToggle : bool
	"""True for toggle parameters."""
	style : str
	"""Describes the behavior and contents of the custom parameter. Example ```'Float'</code>, <code>'Int'</code>, <code>'Pulse'</code>, <code>'XYZ'```, etc."""
	par : parameter.Par
	"""Parameters of parameter.Par"""
	def copy(self, Par) -> None: 
		"""Copy the specified [[Par Class|parameter]].

* Par - The parameter to copy.

```python


op('geo1').par.tx.copy( op('geo2').par.tx )


```"""
		pass
	def eval(self, ) -> any: 
		"""Evaluate a parameter. This value may be derived by the parameter's constant value, expression, or export, dependent on its mode.

```python


a = op('geo1').par.tx.eval()


```




Calling ```eval``` on an OP parameter that can hold multiple OPs will return a single OP if there is only 1 result, a list of OPs if there are more than 1, and None if there are no results."""
		pass
	def evalNorm(self, ) -> any: 
		"""Similar to eval() but the returns the normalized slider value."""
		pass
	def evalExpression(self, ) -> any: 
		"""Evaluate the expression portion of a parameter, if it contains one. This will ignore any exports, etc.

```python


a = op('geo1').par.tx.evalExpression()


```


'''Note''': the results of evalExpression is always the expression's Python return value, which can be slightly different than ```Par.eval()</code>. For example, in parameters that hold an operator, <code>.eval()``` will always return an operator if it exists, even if the expression actually returns a string path. The evalExpression function would return the string path.



To evaluate an arbitrary expression string, that is not inside a parameter, see [[OP Class|OP]].evalExpression."""
		pass
	def evalExport(self, ) -> any: 
		"""Evaluate the export portion of a parameter, if it contains one. This will ignore any expressions, etc.

```python


a = op('geo1').par.tx.evalExport()


```"""
		pass
	def evalOPs(self, ) -> list: 
		"""Evaluate the parameter as series of operators. This is useful for a custom  parameter that specifies a list of operator paths for example.

```python


a = op('base1').par.Paths.evalOPs()


```"""
		pass
	def pulse(self, value, frames=nframes, seconds=nseconds) -> None: 
		"""Pulsing sets a parameter to the specific value, cooks the operator, then restores the parameter to its previous value.

For pulse type parameters no value is specified or used.

* value - (Optional) The value to pulse this parameter with, default is 1.

* frames - (Optional) Number of frames before restoring the parameter to its original value.

* seconds - (Optional) Number of seconds before restoring the parameter to its original value.

```python


op('moviein1').par.reload.pulse(1) #set the reload toggle, then cook

op('glsl1').par.loadvariablenames.pulse() #activate the pulse parameter

op('geo1').par.ty.pulse(2, frames=120) #pulse geometry ty for 120 frames

op('text1').par.text.pulse('GO!', seconds=3) #pulse text TOP string field, for 3 seconds

op('noise').par.type.pulse('random', seconds=0.5) #pulse noise meny type for half a second


```"""
		pass
	def destroy(self, ) -> None: 
		"""Destroy the parameter referenced by this Par. An exception will be raised if the parameter has already been destroyed. Only custom and sequential parameters can be destroyed.  Destroying a sequential parameter will destroy its entire block. Note: When any parameter is destroyed, any existing parameter objects will be invalid and should be re-fetched."""
		pass
	pass


class PanelValue():
	"""A PanelValue describes an instance to a [[Panel Value]].  They can be accessed through a component's [[Panel|panel]] member, and are used in the [[Panel Execute DAT]].



For a list of available panel values, see: [[Panel Value]]."""
	name : str
	"""The name of the panel value. See [[Panel Value]] for the list of possible names. name is a string."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	val : value
	"""Get or set the panel value."""
	valid : bool
	"""True if the referenced panel value currently exists, False if it has been deleted."""
	par : parameter.PanelValue
	"""Parameters of parameter.PanelValue"""
	pass


class Panel():
	"""The Panel class manages Panel Components, and is used to access the state of a panel via its [[PanelValue Class|Panel Value Class]].



For a list of available panel values, see: [[Panel Value]]."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs.



In addition to the above, this object contains a member for each panel value in the component.

```python


a = op('button1').panel.u


```
"""
	par : parameter.Panel
	"""Parameters of parameter.Panel"""
	pass


class Page():
	"""The Page Class describes the list of custom [[Par Class|parameters]] contained on a page. Pages are created on components via the COMP Class. See also the guide [[Custom Parameters]].



Methods that create parameters return a list of [[Par Class|parameters]] that were created.



To view individual attributes of each parameter such as default, min, max, etc, see the [[Par Class]] documentation.



Pages can be accessed like a Python list of parameters:

```python


page = op('button1').pages[0]	# get the page object

print(len(page))				# number of parameters on the page 

debug(page[0])					# first parameter on the page

for p in pages:

	debug(m.description)		# print all the parameters on the page


```
"""
	name : bool
	"""Get or set the name of the page."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	parGroups : list
	"""A list of [[ParGroup Class|parameter groups]] on this page. A ParGroup is the set of parameters on one line."""
	parTuplets : list
	"""The list of [[Par Class|parameter]] tuplets on this page. A [[tuplet]] is the set of parameters on one line."""
	pars : list
	"""The list of [[Par Class|parameters]] on this page."""
	index : int
	"""The numeric index of this page."""
	isCustom : bool
	"""Boolean for whether this page is custom or not."""
	par : parameter.Page
	"""Parameters of parameter.Page"""
	def appendOP(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a node reference type [[Par Class|parameter]]. This parameter will accept references to any operator.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendCOMP(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a COMP node reference type [[Par Class|parameter]]. This parameter will only accept references to COMPs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendOBJ(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a 3D Object COMP node reference type [[Par Class|parameter]]. This parameter will only accept references to 3D Object COMPs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendObject(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a 3D Object COMP node reference type [[Par Class|parameter]]. This parameter will only accept references to 3D Object COMPs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendPanelCOMP(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a Panel COMP node reference type [[Par Class|parameter]]. This parameter will only accept references to Panel COMPs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendTOP(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a TOP node reference type [[Par Class|parameter]]. This parameter will only accept references to TOPs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendCHOP(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a CHOP node reference type [[Par Class|parameter]]. This parameter will only accept references to CHOPs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendSOP(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a SOP node reference type [[Par Class|parameter]]. This parameter will only accept references to SOPs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendMAT(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a MAT node reference type [[Par Class|parameter]]. This parameter will only accept references to MATs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendDAT(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a DAT node reference type [[Par Class|parameter]]. This parameter will only accept references to DATs, and will refuse operators of other families.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendInt(self, name, label=None, size=1, order=None, replace=True) -> ParGroup: 
		"""Create a integer type [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* size - (Keyword, Optional) Set the number of values associated with the parameter. When greater than 1, the parameter will be shown as multiple float fields without a slider and multiple parameters will be created with the index of the parameter appended to the parameter name, starting at 1.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendFloat(self, name, label=None, size=1, order=None, replace=True) -> ParGroup: 
		"""Create a float type [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* size - (Keyword, Optional) Set the number of values associated with the parameter. When greater than 1, the parameter will be shown as multiple float fields without a slider and multiple parameters will be created with the index of the parameter appended to the parameter name, starting at 1.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendXY(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a XY position type [[Par Class|parameter]]. Similar to creating a float parameter with size=2, but with more appropriate default naming.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendXYZ(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a XYZ position type [[Par Class|parameter]]. Similar to creating a float parameter with size=3, but with more appropriate default naming.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendXYZW(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a XYZW position type [[Par Class|parameter]]. Similar to creating a float parameter with size=4, but with more appropriate default naming.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendWH(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a WH size type [[Par Class|parameter]]. Similar to creating a float parameter with size=2, but with more appropriate default naming.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendUV(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a UV 2D texture type [[Par Class|parameter]]. Similar to creating a float parameter with size=2, but with more appropriate default naming.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendUVW(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a UVW 3D texture type [[Par Class|parameter]]. Similar to creating a float parameter with size=3, but with more appropriate default naming.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendRGB(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a RGB color type [[Par Class|parameter]]. Similar to creating a float parameter with size=3, but with more appropriate default naming.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendRGBA(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a RGBA color type [[Par Class|parameter]]. Similar to creating a float parameter with size=4, but with more appropriate default naming.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendStr(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a string type [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendStrMenu(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a menu type [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendMenu(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a menu type [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

To set the actual menu entries, use the [[Par Class|Par]] members: .menuNames and .menuLabels.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendFile(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a file reference type [[Par Class|parameter]]. Has built-in functionality to open a new file picker window.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendFolder(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a folder reference type [[Par Class|parameter]]. Has built-in functionality to open a new folder picker window.

Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendPulse(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a pulse button type [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendMomentary(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a momentary button type [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendToggle(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a toggle button type [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendPython(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a python expression [[Par Class|parameter]]. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendPar(self, name, par=None, label=None, order=None, replace=True) -> ParGroup: 
		"""Create a parameter with attributes copied from an existing parameter. Returns the created [[ParGroup Class|parameter group]] object.

* name - The name of the parameter. Built-in names can be used as they will be automatically adjusted to match proper custom name casing (begin with uppercase letter followed by lowercase letters and numbers only).

* par - (Keyword, Optional) The parameter to copy attributes from. If none specified, a default parameter created.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def appendHeader(self, name, label=None, order=None, replace=True) -> ParGroup: 
		"""Returns the created [[ParGroup Class|parameter group]] object. Only the value will be shown, not its label.

* name - The name of the parameter.

* label - (Keyword, Optional) The displayed label of the parameter, default will use the name argument.

* order - (Keyword, Optional) Specify the display order of the parameter, default is highest.

* replace - (Keyword, Optional) By default, replaces parameter with fresh attributes. If False, it errors if the parameter already exists."""
		pass
	def destroy(self, ) -> None: 
		"""Destroy the page this object refers to, and all its parameters."""
		pass
	def sort(self, pargoup1, pargroup2, pargroup3, *args) -> None: 
		"""Reorder custom parameter groups or parameters in specified order.

```'python'


n = op('base1')

page = n.appendCustomPage('Custom1')

page.sort('Speed','Color','Value')


```"""
		pass
	pass


class ParGroup():
	"""The ParGroup class describes an instance of a single Parameter.



See also [[Custom Parameters]]."""
	bindExpr : tuple
	"""Get or set expressions that return a Parameter object. This can be used to bind this parameter's constant values to the referenced parameters.



Example:

```python
p.bindExpr = ('op('geo1').par.tx', 'op('geo1').par.ty', 'op('geo1').par.tz')
```
  

        Note the outside quotes, as bindExpr is an expression, not an object."""
	bindMaster : tuple
	"""The objects to which this parameter is bound to, possibly None."""
	bindRange : bool
	"""Get or set parameter's range binding state. If True, min, max, clampMin, clampMax, normMin, normMax, normVal values will be based on master bind parameter. Can only be set on Custom Parameters."""
	bindReferences : tuple
	"""The (possibly empty) lists of objects which bind to this parameter."""
	clampMax : tuple
	"""Get or set the parameter's numerical clamping behaviors. If set to <syntaxhighlight lang=python inline=true>clampMax = True</syntaxhighlight>, the parameter will clamp on the upper end at the value specified in max Can only be set on Custom Parameters."""
	clampMin : tuple
	"""Get or set the parameter's numerical clamping behaviors. If set to <syntaxhighlight lang=python inline=true>clampMin = True</syntaxhighlight>, the parameter will clamp on the lower end at the value specified in min Can only be set on Custom Parameters."""
	collapsable : bool
	"""Returns True if the parameter is collapsable."""
	collapser : bool
	"""Returns True if the parameter is a parent of collapsable parameters (ie. a collapser)."""
	default : tuple
	"""Get or set the parameter's default values. Can only be set on Custom Parameters. Only one of default, defaultExpr can be set."""
	defaultExpr : tuple
	"""Get or set the parameter's default expressions. Can only be set on Custom Parameters. Only one of default, defaultExpr can be set.

```python


# value defaults to this expression.

op('base1').parGroup.Size.defaultExpr = ('me.time.frame', 'me.time.frame', 'me.time.frame')


```
"""
	enable : bool
	"""Get or set the parameter's enable state. Can only be set on Custom Parameters."""
	enableExpr : string
	"""Get or set an expression that controls the enable state for this parameter group.

```python


p.enableExpr = 'me.par.X.menuIndex == 5'


```


Note the outside quotes, as this is an expression, not an object."""
	exportOP : tuple
	"""The operators exporting to this parameter."""
	exportSource : tuple of cell, channel or None
	"""The objects exporting to this parameter. Examples: Cell, Channel or None."""
	expr : tuple
	"""Get or set the non-evaluated expressions only. To get the parameter's current values, regardless of the Parameter Mode (constant, expression, export or bound), use the eval() method described below.

```python


op('geo1').parGroup.t.expr = ('absTime.frame', 'absTime.frame', 'absTime.frame')  

# set to match current frame


```


When setting this member, the parameter will also be placed in expression mode. See mode member below.

'''NOTE:''' For convenience, the expression is placed in double-quotes so you can safely put in expressions containing single quotes. 'a' and 'a' have the same effect of enclosing strings in python."""
	help : string
	"""Get or set a custom parameter's help text. To see any parameter's help, rollover the parameter while holding the Alt key."""
	isDefault : bool
	"""True when the parameter value, expression and mode are in their default settings."""
	isCustom : bool
	"""True for Custom Parameters."""
	isFloat : bool
	"""True for floating point numeric parameters."""
	isInt : bool
	"""True for integer numeric parameters."""
	isMenu : bool
	"""True for menu parameters."""
	isMomentary : bool
	"""True for momentary parameters."""
	isNumber : bool
	"""True for numeric parameters."""
	isOP : bool
	"""True for OP parameters."""
	isPulse : bool
	"""True for pulse parameters."""
	isPython : bool
	"""True for python parameters."""
	isString : bool
	"""True for string parameters."""
	isToggle : bool
	"""True for toggle parameters."""
	label : string
	"""Get or set the parameter's label.

```python


op('myOperator').parGroup.Custompar.label = 'Translate'


```
 

Can only be set on Custom Parameters."""
	max : tuple
	"""Get or set the parameter's numerical maximum values. The parameter's values will be clamped at that maximum if <syntaxhighlight lang=python inline=true>clampMax = True</syntaxhighlight>. Can only be set on Custom Parameters."""
	menuIndex : tuple
	"""Get or set a tuple of menu constant values by their indices."""
	menuLabels : tuple
	"""Get or set a tuple of lists of all possible menu choice labels. In the case of non menu parameters, None(s) are returned. Can only be set on Custom Parameters."""
	menuNames : tuple
	"""Get or set a tuple of lists of all possible menu choice names. In the case of non menu parameters, None(s) are returned. Can only be set on Custom Parameters."""
	menuSource : tuple
	"""Get or set a tuple of expressions that returns objects with ```.menuItems</code> <code>.menuNames``` members.  This can be used to create a custom menu whose entries dynamically follow that of another menu for example."""
	min : tuple
	"""Get or set the parameter's numerical minimum values. The parameter's values will be clamped at that minimum if <syntaxhighlight lang=python inline=true>clampMin = True</syntaxhighlight> for the particular Par. Can only be set on Custom Parameters."""
	mode : tuple
	"""Get or set the parameter's evaluation modes.

```python


op('geo1').parGroup.t.mode = (ParMode.EXPRESSION, ParMode.EXPRESSION, ParMode.EXPRESSION)


```


The modes are one of:  ```ParMode.CONSTANT</code>, <code>ParMode.EXPRESSION</code>, or <code>ParMode.EXPORT</code>, or <code>ParMode.BIND```.

See [[Parameter_Dialog#Working_with_Parameter_Modes]] for more information."""
	name : string
	"""Get or set the parameter's unique name.

<syntaxhighlight lang=python

>op('myOperator').parGroup.Custompar.name = 'Translate'

</syntaxhighlight> 

Can only be set on Custom Parameters."""
	normMax : tuple
	"""Get or set the parameter's maximum slider values if the parameter is a numerical slider. Can only be set on Custom Parameters."""
	normMin : tuple
	"""Get or set the parameter's minimum slider values if the parameter is a numerical slider. Can only be set on Custom Parameters."""
	normVal : tuple
	"""Get or set the parameter's values as a normalized slider position. Can only be set on Custom Parameters."""
	order : int
	"""Get or set the parameter's position on the parameter page.  Can only be set on Custom Parameters."""
	owner : OP
	"""The OP to which this object belongs."""
	page : Page
	"""Get or set the parameter page the custom parameter is part of. Can only be set on Custom Parameters."""
	password : bool
	"""Get or set the parameter's password mode. When True all text is rendered as asterisks. Can only be set on Custom string, int or float parameters. Custom Parameters."""
	prevMode : tuple
	"""The parameter's previous evaluation modes."""
	readOnly : bool
	"""Get or set the parameter's read only status. When True the parameter cannot be modified through the UI, only scripting."""
	displayOnly : bool
	"""Get or set the parameter's displayOnly state. Can only be set on Custom Parameters."""
	sequence : any
	"""The set of sequential parameter blocks this parameter belongs to, or None."""
	startSection : bool
	"""Get or set the parameter's separator status. When True a visible separator is drawn between this parameter and the ones preceding it. Can only be set on Custom Parameters."""
	style : string
	"""Describes the behavior and contents of the custom parameter. Example 'Float', 'Int', 'Pulse', 'XYZ', etc."""
	subLabel : tuple
	"""Returns the names of the sub-label."""
	val : tuple
	"""Get or set the constant values of the parameter only. To get the parameter's current values, regardless of the Parameter Modes (```constant</code>, <code>expression</code>, <code>export</code> or <code>bound```), use the eval() method described below.

```python


op('geo1').parGroup.t.val   # the constant values 

op('geo1').parGroup.t.eval()   # the evaluated parameter

op('geo1').parGroup.t.val = (1,2,3)

op('geo1').parGroup.t = (1,2,3)  #equivalent to above, more concise form


```


When setting this member, the parameter will also be placed in constant mode.  See mode member below.

To set a menu value by its index, use the menuIndex member as described below."""
	valid : bool
	"""True if the referenced parameter currently exists, False if it has been deleted."""
	index : int
	"""The parameter's order in the list."""
	par : parameter.ParGroup
	"""Parameters of parameter.ParGroup"""
	def copy(self, ParGroup) -> None: 
		"""Copy the specified parameter.

*  ParGroup - The parameter to copy.

```python
op('geo1').parGroup.t.copy( op('geo2').parGroup.t )
```"""
		pass
	def destroy(self, ) -> None: 
		"""Destroy the parameter referenced by this ParGroup. An exception will be raised if the parameter has already been destroyed. Only custom and sequential parameters can be destroyed.  Destroying a sequential parameter will destroy its entire block. Note: When any parameter is destroyed, any existing parameter objects will be invalid and should be re-fetched."""
		pass
	def eval(self, ) -> tuple: 
		"""Evaluate a parameter group. This value may be derived by the parameter group's constant value, expression, or export, dependent on its mode.

```python
a = op('geo1').parGroup.t.eval()
```"""
		pass
	def evalExport(self, ) -> tuple: 
		"""Evaluate the export portions of a parameter, if it contains any. This will ignore any expressions, etc.

```python
a = op('geo1').parGroup.t.evalExport()
```"""
		pass
	def evalExpression(self, ) -> tuple: 
		"""Evaluate the expression portions of a parameter, if it contains any. This will ignore any exports, etc.

```python
a = op('geo1').parGroup.t.evalExpression()
```


To evaluate an arbitrary expression string, that is not inside a parameter, see [[OP Class#evalExpression|OP.evalExpression]]."""
		pass
	def evalNorm(self, ) -> tuple: 
		"""Similar to eval() but the returns the normalized slider values."""
		pass
	def evalOPs(self, ) -> any: 
		"""Evaluate the parameter as series of operators. This is useful for a custom  parameter that specifies a list of operator paths for example.

```python
a = op('base1').parGroup.Paths.evalOPs()
```"""
		pass
	def pars(self, pattern) -> list: 
		"""Returns a (possibly empty) list of parameter objects that match the pattern.

*  pattern - Is a string following the Pattern Matching rules, specifying which parameters to return.

```python


# translate parameters

newlist = op('geo1').parGroup.t.pars('t?')


```"""
		pass
	pass


class packTOP(TOP,OP):
	""""""
	par : parameter.packTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.packTOP & parameter.TOP & parameter.OP"""
	pass


class overTOP(TOP,OP):
	""""""
	par : parameter.overTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.overTOP & parameter.TOP & parameter.OP"""
	pass


class outTOP(TOP,OP):
	""""""
	par : parameter.outTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.outTOP & parameter.TOP & parameter.OP"""
	pass


class outSOP(SOP,OP):
	""""""
	par : parameter.outSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.outSOP & parameter.SOP & parameter.OP"""
	pass


class outsideTOP(TOP,OP):
	""""""
	par : parameter.outsideTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.outsideTOP & parameter.TOP & parameter.OP"""
	pass


class opviewerTOP(TOP,OP):
	""""""
	par : parameter.opviewerTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.opviewerTOP & parameter.TOP & parameter.OP"""
	pass


class openvrTOP(TOP,OP):
	""""""
	par : parameter.openvrTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.openvrTOP & parameter.TOP & parameter.OP"""
	pass


class openvrSOP(SOP,OP):
	""""""
	par : parameter.openvrSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.openvrSOP & parameter.SOP & parameter.OP"""
	pass


class opencolorioTOP(TOP,OP):
	""""""
	par : parameter.opencolorioTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.opencolorioTOP & parameter.TOP & parameter.OP"""
	pass


class Monitors():
	"""The Monitors class describes the set of all installed [[Monitor Class|monitor objects]]. It can be accessed with the monitors object, found in the automatically imported [[td Module|td module]].   It operates much like a Python list of monitor objects.

```python


print(len(monitors))		# number of monitors 

print(monitors[0])			# first monitor in the list

for m in monitors:

	print(m.description)	# print all installed monitors' descriptions


```
"""
	primary : int
	"""The primary [[Monitor Class|monitor]] display."""
	width : int
	"""The width of the combined monitor area, measured in pixels."""
	height : int
	"""The height of the combined monitor area, measured in pixels."""
	left : int
	"""The leftmost edge of the combined monitor area, measured in pixels."""
	right : int
	"""The rightmost edge of the combined monitor area, measured in pixels."""
	top : int
	"""The topmost position of the combined monitor area, measured in pixels."""
	bottom : int
	"""The bottommost position of the combined monitor area, measured in pixels."""
	par : parameter.Monitors
	"""Parameters of parameter.Monitors"""
	def locate(self, x,y) -> any: 
		"""Return the [[Monitor Class|monitor]] at the specified mouse coordinates, or None."""
		pass
	def refresh(self, ) -> None: 
		"""Causes the application to behave as if a monitor device has changed. [[Monitors DAT]] and other sources will be updated. This is typically done automatically by the operating system, but in special cases can be triggered manually with this method."""
		pass
	pass


class Monitor():
	"""The Monitor class describes a single instance of a monitor display. They can be accessed from the [[Monitors Class|monitors]] object."""
	index : int
	"""The monitor position in the list."""
	isPrimary : bool
	"""Returns true, if this monitor is the primary display."""
	isAffinity : bool
	"""Returns true, if this monitor is connected to the GPU that has been selected for GPU Affinity. Always True if GPU Affinity is not used."""
	width : int
	"""The width of the monitor area, measured in pixels."""
	height : int
	"""The height of the monitor area, measured in pixels."""
	left : int
	"""The position of left edge of the monitor area, measured in pixels."""
	right : int
	"""The position of right edge of the monitor area, measured in pixels."""
	top : int
	"""The position of top edge of the monitor area, measured in pixels."""
	bottom : int
	"""The position of bottom edge of the monitor area, measured in pixels."""
	displayName : str
	"""The unique display name associated with this monitor."""
	description : str
	"""A description of the monitor or its display adapter."""
	dpiScale : float
	"""The DPI Scaling factor the monitor is current set to."""
	scaledWidth : int
	"""The width of the monitor area, measured in points."""
	scaledHeight : int
	"""The height of the monitor area, measured in points."""
	scaledLeft : int
	"""The position of left edge of the monitor area, measured in points."""
	scaledRight : int
	"""The position of right edge of the monitor area, measured in points."""
	scaledTop : int
	"""The position of top edge of the monitor area, measured in points."""
	scaledBottom : int
	"""The position of bottom edge of the monitor area, measured in points."""
	serialNumber : str
	"""The serial number name associated with this monitor. May be blank."""
	refreshRate : float
	"""The refresh rate the monitor is currently running at."""
	par : parameter.Monitor
	"""Parameters of parameter.Monitor"""
	pass


class MOD():
	"""The MOD class provides access to Module On Demand object, which allows [[DAT|DATs]] to be dynamically imported as modules.  It can be accessed with the mod object, found in the automatically imported [[td Module|td module]].  Alternatively, one can use the regular python statement: import.

Use of the import statement is limited to modules in the search path, where as the mod format allows complete statements in one line, which is more useful for entering expressions.  Also note that DAT modules cannot be organized into packages as regular file system based python modules can be."""
	par : parameter.MOD
	"""Parameters of parameter.MOD"""
	pass


class Matrix():
	"""The matrix class holds a single 4x4 matrix for use in transformations. The matrix's data layout is in [http://en.wikipedia.org/wiki/Column-major_order#Column-major_order column-major format], which is to say that the matrix is multiplied from the left of [[Vector Class|vectors]] and [[Position Class|positions]]. The translation values are stored in the last column of the matrix.

A matrix is created with this line, and will always be initialized to the identity matrix.

```python


m = tdu.Matrix()


```


You can also initialize a matrix with an initial set of values. Valid arguments for initialization is another tdu.Matrix, a list of 16 values or 4 lists of 4 values. The entries are specified column-by-column. For example the following lines of code will produce the shown matrix

```python


m = tdu.Matrix([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])

# or

m = tdu.Matrix([1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16])


```


```python


# matrix values

1  5  9   13

2  6  10  14

3  7  11  15

4  8  12  16


```


You can also get transformation and projection matrices from [[ObjectCOMP Class|Object COMP]] and [[CameraCOMP Class|Camera COMP]] by using the various methods such as ```transform(), pretransform(), projection()```."""
	vals : float
	"""Get or set the set of Matrix values."""
	rows : list of lists
	"""The list of Matrix rows, each a list of values."""
	cols : list of lists
	"""The list of Matrix columns, each a list of values."""
	par : parameter.Matrix
	"""Parameters of parameter.Matrix"""
	def transpose(self, ) -> None: 
		"""Transpose the values in the matrix.

```python


m.transpose() # m now contains the transpose of the matrix


```"""
		pass
	def getTranspose(self, ) -> None: 
		"""Returns the transpose of the matrix, leaving the matrix itself unchanged.

```python


m2 = m.getTranspose()


```"""
		pass
	def invert(self, ) -> None: 
		"""Inverts the values in the matrix.

```python


m.invert() # m now contains the inverse of the matrix


```"""
		pass
	def getInverse(self, ) -> any: 
		"""Returns the inverse of the matrix, leaving the matrix itself unchanged.

```python


m2 = m.getInverse()


```"""
		pass
	def determinant(self, ) -> float: 
		"""Returns the determinant of the matrix.

```python


l = m.determinant()


```"""
		pass
	def mapUnitSquareToQuad(self, blX, blY, brX, brY, tlX, tlY, trX, trY) -> None: 
		"""Set the matrix to be a projection matrix that maps coordinates from to a unit square (0,0) -> (1,1) space to a space defined by an arbitrary quadrilateral (blX, blY) -> (trX, trY). The 4 corners of the quadrilateral are given ('bl' means bottom left, 'tr' means top right etc.)."""
		pass
	def mapQuadToUnitSquare(self, blX, blY, brX, brY, tlX, tlY, trX, trY) -> None: 
		"""Is the inverse of mapUnitSquareToQuad(). Mapping coordinates in an arbitrary quadrilateral into a space defined by the unit square."""
		pass
	def fillTable(self, tableDAT) -> None: 
		"""Fill in the contents of a table from the matrix which the method is called upon.

* tableDAT - The table to be filled."""
		pass
	def numpyArray(self, ) -> any: 
		"""Returns this matrix as a 4x4 NumPy array."""
		pass
	def identity(self, ) -> None: 
		"""Replaces the values in the matrix with the [http://en.wikipedia.org/wiki/Identity_matrix identity matrix].

```python


m.identity() # now contains the identity matrix


```"""
		pass
	def copy(self, ) -> any: 
		"""Returns a new matrix that is a copy of the matrix.

```python


newM = m.copy() # newM will have the same values as m, m is unchanged


```"""
		pass
	def translate(self, tx, ty, tz, fromRight=False) -> None: 
		"""Multiplies the current matrix by a new translation matrix created from tx, ty and tz. The translation is applied from the left of the matrix by default. That is to say, if T is the new translation matrix, and M is the current matrix, then the result of this operation is M = T *  M.

* tx, ty, tz - The translation value in each axis.

* fromRight - (Keyword, Optional) If True, the translation matrix will be multiplied from the right instead of the left.

```python


m = tdu.Matrix()

m.translate(5, 0, 10)


```"""
		pass
	def rotate(self, rx, ry, rz, fromRight=False, pivot=None) -> None: 
		"""Multiplies the current matrix by 3 rotation matrices, first a rotation around the X axis by rx degrees, followed by a rotation around the Y axis by ry degrees, followed by the same for rz. The rotation values are in degrees. The rotation is applied from the left of the matrix by default. So if M is the current matrix, then the result of this operation is M = RZ *  RY *  RX *  M.

* rx, ry, rz - The rotation value around each X, Y and Z axis. The value is in degrees. The rotation is applied in XYZ order.

* fromRight - (Keyword, Optional) If True, the rotation matrix will be multiplied from the right instead of the left. In this case the operation is M = M *  RZ *  RY *  RX.

* pivot - (Keyword, Optional) If given, the rotation will be applied around the given pivot. The pivot should be a Vector, Position or a list with 3 entries.

```python


m = tdu.Matrix()

m.rotate(45, 0, 0)



m = tdu.Matrix()

m.rotate(0, 0, 90, pivot=[0, 5, 0])



m = tdu.Matrix()

p = tdu.Position(0, 5, 0)

m.rotate(0, 90, 0, pivot=p)


```"""
		pass
	def rotateOnAxis(self, rotationAxis, angle, fromRight=False, pivot=None) -> None: 
		"""Multiplies the current matrix by a new rotation matrix created by rotation angle degrees around the axis specified by rotationAxis. The angle is in degrees. The rotation is applied from the left of the matrix by default. That is to say, if R is the new rotation matrix specified by rotationAxis and angle, and M is the current matrix, then the result of this operation is M = R *  M.

* rotationAxis - A axis to rotate around. This should be a Vector or a list with 3 entries. It does not need to be normalized.

* angle - The amount to rotate around the axis, specified in degrees.

* fromRight - (Keyword, Optional) If True, the rotation matrix will be multiplied from the right instead of the left.

* pivot - (Keyword, Optional) If given, the rotation will be applied around the given pivot. The pivot should be a Vector, Position or a list with 3 entries."""
		pass
	def scale(self, sx, sy, sz, fromRight=False, pivot=None) -> None: 
		"""Multiplies the current matrix by a scale matrix created from sx, sy and sz. The scale is applied from the left of the matrix by default. That is to say, if S is the new scale matrix, and M is the current matrix, then the result of this operation is M = S *  M.

* sx, sy, sz - The scale value along each X, Y and Z axis.

* fromRight - (Keyword, Optional) If True, the scale matrix will be multiplied from the right instead of the left.

* pivot - (Keyword, Optional) If given, the scale will be applied around the given pivot. The pivot should be a Vector, Position or a list with 3 entries.

```python


m = tdu.Matrix()

m.scale(2, 1, 1)



m = tdu.Matrix()

m.scale(2, 1, 2, pivot=[0, 5, 0])



m = tdu.Matrix()

p = tdu.Position(0, 5, 0)

m.scale(1, 2, 1, pivot=p)


```"""
		pass
	def lookat(self, eyePos, target, up) -> None: 
		"""Multiplies the current matrix by a lookat matrix created using the given values to the matrix. The lookat matrix is applied from the left of the matrix by default. That is to say, if L is the new lookat matrix, and M is the current matrix, then the result of this operation is M = L *  M. The values for to parameters can be given as anything that can be treated as a list of 3 values. E.g a tdu.Vector, tdu.Position or simply a list of size 3.

* eyePos - The position in space of the eye/camera.

* target - The position in space that should be looked at, from the eyePos.

* up - The Up vector. Ensure the up vector isn't pointing in the same direction as the lookat direction.

```python


m = tdu.Matrix()

eyeP = tdu.Position(0, 0, -5)

target = tdu.Position(0, 5, 5)

up = tdu.Position(0, 1, 0)

m.lookat(eyeP, target, up)


```"""
		pass
	def decompose(self, ) -> any: 
		"""Decomposes the matrix into its scale, rotate and translate values. These are the same as the translate, rotate and scale that are in the [[Geometry COMP]] and other Object components. However due to rotations being able to be solved in different ways, it's likely a decomposed transform matrix from a Geometry COMP will not have the same values as its parameter. The resulting transform is the same though. This function returns a tuple of tuples (3 tuples), which are the scale, rotate and translate values respectively.

```python


s, r, t = m.decompose()


```"""
		pass
	def projectionFrustum(self, left, right, bottom, top, near, far) -> None: 
		"""Replaces the contents of the matrix with a projection matrix using the given frustum extents. The left, right, bottom, top extents are located on the near plane. The depth range generated by this matrix will be [0,1] from near to far, as is required by Vulkan."""
		pass
	def projectionFovX(self, fovX, aspectX, aspectY, near, far) -> None: 
		"""Replaces the contents of the matrix with a projection matrix defined by the FOV(given in degrees), an aspect ratio and near/far planes.  The depth range generated by this matrix will be [0,1] from near to far, as is required by Vulkan.

* fovX - The horizontal FOV, specified in degrees.

* aspectX, aspectY - The aspect ration values. These can be something like 16 and 9 for an aspect or the render resolution such as 1920 and 1080. The results will be the same for the same ratio."""
		pass
	def projectionStereo(self, ipd, convergeZ, fovX, aspectX, aspectY, near, far, rightEye = false) -> None: 
		"""Replaces the contents of the matrix with an asymetrical projection matrix suitable for stereo rendering. The left eye's projection matrix is given by default, set rightEye=True to get the right eye's instead. For proper rendering, the cameras will also need to be translated in X by -ipd/2 and +ipd/2 for the left and right eyes respectively.  The depth range generated by this matrix will be [0,1] from near to far, as is required by Vulkan.

* ipd - Interpupillary distance of the user, generally specified in meters. Typically between 0.05 and 0.08

* covergeZ - distance in Z from the camera where the stereo convergence should occur, in the same units as ipd.

* aspectX, aspectY - The aspect ratio values. These can be something like 16 and 9 for an aspect or the render resolution such as 1920 and 1080. The results will be the same for the same ratio.

* rightEye - (Keyword, Optional) If set to True, the matrix will contain the projection for the right eye, otherwise it will contain the projection for the left eye."""
		pass
	def [row, column] -> float: 
		"""Gets or sets the specified entry in the matrix.

```python


tx = m[0, 3]

m[0, 3] = tx + 5


```"""
		pass
	def Matrix * Matrix -> any: 
		"""Performs a matrix multiplication returns the results in a new matrix.

```python


newM = m1 *  m2


```"""
		pass
	def Matrix - Matrix -> any: 
		"""Subtracts the matrices, component-by-component, and returns the results in a new matrix."""
		pass
	def Matrix + Matrix -> any: 
		"""Adds the matrices, component-by-component, and returns the results in a new matrix"""
		pass
	def tdu.Matrix * tdu.Vector -> any: 
		"""Multiplies the vector by the matrix and returns the a new vector as the result. Since a Vector is direction only and has no notion of a position, the translate part of the matrix does not get applied to the vector.

```python


newV = M *  v


```"""
		pass
	def tdu.Matrix * tdu.Position -> any: 
		"""Multiplies the position by the matrix and returns the a new position as the result. If the matrix was not an transformation matrix, such as a projection matrix instead, the perspective divide by W will automatically be applied to X, Y and Z.

```python


newP = M *  p


```"""
		pass
	pass


class ListAttributes():
	"""The ListAttributes class describes a set of [[ListAttribute Class|list attribute objects]] for cells, rows, columns or table. It can be accessed from a [[listCOMP Class|List Component]].



Access to individual List Attributes depends on what type: row, col, or cell:

```python


rowAttribs = op('list1').rowAttribs		# get the ListAttributes object for rows

print(len(rowAttribs))					# number of rows 

print(rowAttribs[0].bgColor)			# rows are accessed by row #. 

										# This prints the background color settings for the first row



colAttribs = op('list1').colAttribs		# get the ListAttributes object for columns

print(len(colAttribs))					# number of columns 

print(colAttribs[0].bgColor)			# cols are accessed by column #. 

										# This prints the background color settings for the first column



cellAttribs = op('list1').cellAttribs	# get the ListAttributes object for columns

print(len(cellAttribs))					# total number of cells 

print(colAttribs[0,2].bgColor)			# cells are accessed by [row, col]. 

										# This prints the background color settings for the cell in the first row, third column


```


'''Note:''' The attributes above are the settings for List Component's hierarchical layout technique. This means that cell settings

override row settings, which override column settings, which override table settings. If you want to know the final value in a

given cell, use ```listCOMP.displayAttribs[row, col]```."""
	par : parameter.ListAttributes
	"""Parameters of parameter.ListAttributes"""
	pass


class ListAttribute():
	"""The ListAttribute class describes an attribute defining a cell or set of cells in a [[listCOMP Class|List Component]]."""
	bgColor : tuple(r,g,b,a)
	"""Get or set background color."""
	bottomBorderInColor : tuple(r,g,b,a)
	"""Get or set inside bottom color."""
	bottomBorderOutColor : tuple(r,g,b,a)
	"""Get or set outside bottom color."""
	colStretch : bool
	"""Get or set column stretchiness. When True, colWidth specifies minimum width."""
	colWidth : float
	"""Get or set column width, expressed in pixels."""
	draggable : bool
	"""Get or set whether or not cell is draggable."""
	editable : bool
	"""Get or set whether or not contents are editable. When True, contents can be edited by clicking on the cell."""
	focus : bool
	"""Returns True if the cell/row/column/table is currently being edited."""
	fontFile : string
	"""Get or set font file. VFS embedded files supported as well."""
	fontBold : bool
	"""Get or set whether or not text is rendered in bold font."""
	fontFace : str
	"""Get or set font face. Example 'verdana'."""
	fontItalic : bool
	"""Get or set whether or not text is rendered italicized."""
	fontSizeX : float
	"""Get or set font horizontal size."""
	fontSizeY : float
	"""Get or set font vertical size. If not specified, uses fontSizeX."""
	sizeInPoints : bool
	"""Get or set text size units. When True size is in points, when False it is in pixels."""
	help : str
	"""Get or set help string when rolling over the cell."""
	leftBorderInColor : tuple(r,g,b,a)
	"""Get or set inside left color."""
	leftBorderOutColor : tuple(r,g,b,a)
	"""Get or set outside left color."""
	radio : bool
	"""Returns true if the mouse last selected the cell/row/column/table."""
	rightBorderInColor : tuple(r,g,b,a)
	"""Get or set inside right color."""
	rightBorderOutColor : tuple(r,g,b,a)
	"""Get or set outside right color."""
	rollover : bool
	"""Returns true if the mouse is currently over the cell/row/column/table."""
	rowHeight : float
	"""Get or set row height, expressed in pixels."""
	rowIndent : float
	"""Get or set row indent, expressed in pixels."""
	rowStretch : bool
	"""Get or set row stretchiness. When True, rowWidth specifies minimum width."""
	select : bool
	"""Returns true if the mouse is currently pressed over the cell/row/column/table."""
	text : str
	"""Get or set contents."""
	textColor : tuple(r,g,b,a)
	"""Get or set text color.  Color values must be a tuple with four numeric entries corrresponding to red, green, blue, alpha ie:  (0.3, 06, 0.1, 1.0)"""
	textJustify : JustifyType
	"""Get or set text justification. Value is one of: JustifyType.TOPLEFT, JustifyType.TOPCENTER, JustifyType.TOPRIGHT, JustifyType.CENTERLEFT, JustifyType.CENTER, JustifyType.CENTERRIGHT, JustifyType.BOTTOMLEFT, JustifyType.BOTTOMCENTER, JustifyType.BOTTOMRIGHT"""
	textOffsetX : float
	"""Get or set horizontal text offset."""
	textOffsetY : float
	"""Get or set vertical text offset."""
	top : op
	"""Get or set background image [[TOP Class|TOP]]."""
	topBorderInColor : tuple(r,g,b,a)
	"""Get or set inside top color."""
	topBorderOutColor : tuple(r,g,b,a)
	"""Get or set outside top color."""
	wordWrap : bool
	"""Get or set word wrapping."""
	par : parameter.ListAttribute
	"""Parameters of parameter.ListAttribute"""
	pass


class Licenses():
	"""The Licenses class describes the set of all installed [[License Class|license objects]].  It can be accessed with the licenses object, , found in the automatically imported [[td Module|td module]].

```python


print(len(licenses))	# number of licenses 

print(licenses[0])		# first license in the list

for l in licenses:

	print(l.type)		# print all installed licenses' types


```
"""
	disablePro : bool
	"""When True, the application will run as though no Pro licenses are available.  This can be used to test compatibility with lesser licenses. (See also: [[App Class#Methods|app.addNonCommercialLimit]])"""
	dongles : list
	"""Get the list of dongles connected to the system."""
	machine : str
	"""The computer machine name."""
	systemCode : str
	"""The unique computer system code."""
	isPro : bool
	"""When True, the application is running with a Pro license. It is recommended to use this and isNonCommerical over the type method."""
	isNonCommercial : bool
	"""When True, the application is running with a Non-Commercial license. It is recommended to use this and isPro over the type method."""
	type : str
	"""The highest ranking license type of all installed licenses, some products being 'Pro', 'Non-Commercial', 'Commercial'. See also app.product in [[App Class]]."""
	par : parameter.Licenses
	"""Parameters of parameter.Licenses"""
	def install(self, key) -> bool: 
		"""Install a [[License Class|license]] with the specified key.  Returns True if successful."""
		pass
	pass


class License():
	"""The License class describes a single instance of an installed license.  They can be accessed from the [[Licenses Class|licenses]] object."""
	index : int
	"""The license index in the list."""
	isEnabled : bool
	"""True if the license is locally enabled (That is, it has never been disabled)."""
	isRemotelyDisabled : bool
	"""True if the license has been remotely disabled."""
	key : str
	"""The key sequence."""
	remoteDisableDate : tuple(year, month, date)
	"""The date the license was remotely disabled, expressed as a tuple (year, month, day)."""
	status : int
	"""The numeric status code. Negative values indicate the license is not applicable to the current application. A value of zero indicates it does."""
	statusMessage : str
	"""A description of the status code."""
	systemCode : str
	"""The system code associated with this license."""
	type : str
	"""The license type, e.g. some products being 'Pro', 'Non-Commercial', 'Commercial'. See also app.product in [[App Class]]"""
	updateExpiryDate : tuple(year, month, day)
	"""The date updates for this license expires, expressed as a tuple (year, month, day)."""
	version : int
	"""The numeric license version."""
	par : parameter.License
	"""Parameters of parameter.License"""
	pass


class Group():
	"""An Group describes groups lists of [[Prim Class]] or [[Point Class]]. 



A Group can be created with the [[Group SOP]] or using the <syntaxhighlight lang=python inline=True>createPointGroup(str)</syntaxhighlight> or <syntaxhighlight lang=python inline=True>createPrimGroup(str)</syntaxhighlight> methods of the [[ScriptSOP Class]]."""
	default : tuple
	"""The default values associated with this Group. It returns a tuple item of group points."""
	name : str
	"""Set/gets the group name."""
	owner : OP
	"""Gets the owner of this group."""
	par : parameter.Group
	"""Parameters of parameter.Group"""
	def add(self, Point or Prim or int) -> None: 
		"""Adds a point/primitive to this group. The point or primitive to be added can be specified by a point, primitive object or the index of a point or primitive object."""
		pass
	def discard(self, Point or Prim or int) -> None: 
		"""Removes a point/primitive from this group. The point or primitive to be removed can be specified by a point, primitive object or the index of a point or primitive object."""
		pass
	def destroy(self, ) -> None: 
		"""Destroys the current point/primitive group."""
		pass
	pass


class FileInfo():
	"""The FileInfo object stores a file path and has a few utility properties to provide additional info. It is derived from str, so will work as a Python string, but can be differentiated from a regular string by using <syntaxhighlight lang=python inline=true>isinstance(tdu.FileInfo)</syntaxhighlight>.



Utility properties include:

*  path: filepath string

*  ext: string after and including '.'

*  baseName: the basename of the file

*  fileType: the TD filetype (from tdu.fileTypes)

*  absPath: the absolute path to filepath

*  dir: the containing directory of filepath

*  exists: exists in file-system

*  isDir: is a directory in the file-system

*  isFile: is a file in the file-system"""
	par : parameter.FileInfo
	"""Parameters of parameter.FileInfo"""
	pass


class DongleList():
	"""A list of [[Dongle Class|dongles]] connected to the system. The system instance can be found in ```licenses.dongles```.

```python


dongles = licenses.dongles		# get the DongleList object

print(len(dongles))				# number of Dongles 

print(dongles[0])				# first Dongle in the list

for d in dongles:

	print(d)					# print all Dongles


```
"""
	par : parameter.DongleList
	"""Parameters of parameter.DongleList"""
	def refreshDongles(self, ) -> None: 
		"""Refreshes the list of dongles connected to the system and their product codes."""
		pass
	def encrypt(self, firmCode, productCode, data) -> any: 
		"""Encrypts a string or byte array using a CodeMeter dongle with a given firm code and product code installed on it. If successful it returns a byte array with the encrypted data.

*  firmCode - The firm code to use. It must be present on the dongle.

*  productCode - The product code to use. It must be present on the dongle.

*  data - A string or byte array to encrypt. Must be 16 bytes in size at least."""
		pass
	def decrypt(self, firmCode, productCode, data) -> any: 
		"""Decrypts a string or byte array using a CodeMeter dongle with a given firm code and product code installed on it. If successful it returns a byte array with the decrypted data.

*  firmCode - The firm code to use. It must be present on the dongle.

*  productCode - The product code to use. It must be present on the dongle.

*  data - A string or byte array to decrypt. Must be 16 bytes in size at least."""
		pass
	def productCodeInstalled(self, ) -> bool: 
		"""Returns True if the provided product code is installed on any of the connected dongles."""
		pass
	pass


class Dongle():
	"""A class to interact with a single dongle connected to the system."""
	serialNumber : str
	"""Dongle Serial Number."""
	par : parameter.Dongle
	"""Parameters of parameter.Dongle"""
	def applyUpdate(self, str) -> None: 
		"""Takes an update as a string and applies it to the dongle."""
		pass
	def createUpdateContext(self, ) -> str: 
		"""Returns a string which is the remote programming update context for the dongle."""
		pass
	pass


class Dependency():
	"""A '''[[Dependency]]''' object is a value that automatically causes any expression referencing it to update when the dependency value has changed.  These objects eliminate the need to manually force cook operators referencing values in [[Extensions]] or [[OP_Class#Storage|Storage]] for example.

For information about dependencies in mutable objects (lists, dicts, sets), see '''[[TDStoreTools#Deeply_Dependable_Collections|Deeply Dependable Collections]]'''"""
	val : value
	"""The value associated with this object. Referencing this value in an expression will cause the operator to become dependent on its value. Setting this value will cause those operators to be recooked as necessary."""
	peekVal : value
	"""This returns the same value as .val but does not create a dependency on the value."""
	callbacks : list
	"""A modifiable list of functions. When the Dependency object is modified, it calls each function on the list. Each function is called with a single argument which is a dictionary containing the following:

*  'dependency'- The Dependency that was modified.

*  'prevVal' - The previous value if available.

*  'callback' - This callback function."""
	ops : list
	"""A list of [[OP Class|operators]] currently dependent on the object."""
	listAttributes : list
	"""A list of [[ListAttribute Class|list attributes]] currently dependent on the object."""
	par : parameter.Dependency
	"""Parameters of parameter.Dependency"""
	def modified(self, ) -> None: 
		"""This call is needed when changing not the value itself, but a subcomponent. For example, if Dependency.val is a dictionary, setting any of the members will not notify the dependent operators. A call to modified is necessary."""
		pass
	def [<index or key>] -> any: 
		"""'''Only when the dependency wraps iterable or mapped data such as a list or dictionary''', you can use [] to access the items in the wrapped data.

```python


dep = tdu.Dependency({'fred': 33, 'wilma':39})

print(dep['fred']) # prints '33'. The key to the dictionary works directly on the dependency object.

dep2 = tdu.Dependency(['a', 'd', 'g'])

print(dep[2]) # prints 'g'. The index to the list works directly on the dependency object.


```"""
		pass
	pass


class debug():
	"""The ```debug</code> module provides tools for use with TouchDesigner's builtin <code>debug``` statement. It also contains utilities for customizing those statements and building customized debug output. It is a member of [[Tdu Module]].



You can use the [[Palette:debugControl|debugControl]] component in the palette to set up ```debug``` behavior without using Python."""
	style : types.SimpleNamespace
	"""A namespace containing information about how to process ```debug``` statements. This data is not meant to be changed directly. Instead, use the setStyle function below."""
	par : parameter.debug
	"""Parameters of parameter.debug"""
	def debug(self, *args) -> None: 
		"""Print all args and extra debug info (default is DAT and line number) to texport. To change behavior, use the [[Palette:debugControl|debugControl]] component or setStyle function (below).<br>'''TIP: Always use ```debug</code> instead of <code>print``` when debugging Python scripts.'''"""
		pass
	def setStyle(self, printStyle=None, showDAT=None, showFunction=None, showLineNo=None, suppress=None, formatOverride=None, functionOverride=None) -> None: 
		"""Set the style for the built in TD debug function. Any arguments passed as None will leave that feature unchanged.



:```printStyle```:

::```'pprint'```=convert non-string args to pprint.pformat(arg, indent=4, sort_dicts=False). Makes lists, dicts, etc. easily readable

::```'pprint_sorted'```=convert non-string args to pprint.pformat(arg, indent=4). Makes lists, dicts, etc. easily readable. Dict keys will be alphabetized

::```'repr'```=convert non-string args to repr(arg)

::otherwise, convert non-string args to str(arg)

:```showDAT```: in debug message, show the DAT where debug was called

:```showFunction```: in debug message, show function where debug was called

:```showLineNo```: in debug message, show line number where debug was called

:```suppress```: if True, suppress (don't print) any debug calls

:```formatOverride```: overrides the default message that debug prints. You can use {0}, {1}, and {2} for DAT, function, and line number

:```functionOverride```: overrides the builtin TD debug function. This function will be called with all arguments from any debug calls in your project. Set to False to remove override."""
		pass
	def debugs(self, *args) -> str: 
		"""Return the string that would be printed by the debug function. To change

behavior, use the [[Palette:debugControl|debugControl]] component or setStyle function (above). This is a utility function for building custom debug systems."""
		pass
	def info(self, *args, stackOffset=0) -> list: 
		"""Return all args and extra debug info as processed by the debug function. To

change behavior, use the [[Palette:debugControl|debugControl]] component or setStyle function (above). This is a utility function for building custom debug systems."""
		pass
	pass


class CUDAMemoryShape():
	"""Describes the shape of a CUDA memory segment."""
	width : int
	"""Get/Set the width in pixels of the memory."""
	height : int
	"""Get/Set the height in pixels of the memory."""
	numComps : int
	"""Get/Set the number of color components per pixel of the memory."""
	dataType : numpy data type
	"""Get/Set the data type of each color component, as a numpy data type. E.g numpy.uint8, numpy.float32. Note that for uint8 data types, the channel ordering will be BGRA for 4 component textures. It will be RGBA however for other data types."""
	par : parameter.CUDAMemoryShape
	"""Parameters of parameter.CUDAMemoryShape"""
	pass


class CUDAMemory():
	"""Holds a reference to CUDA memory. The CUDA memory will be deallocated when this class is destructed."""
	ptr : memory address
	"""Returns the raw memory pointer address for the CUDA memory."""
	size : int
	"""Returns the size of the CUDA Memory, in bytes."""
	shape : CUDAMemoryShape
	"""Returns the [[CUDAMemoryShape Class]] describing this CUDA memory. See the help for that class for notes about channel order for different data types."""
	par : parameter.CUDAMemory
	"""Parameters of parameter.CUDAMemory"""
	pass


class Connector():
	"""The Connector class describes the input or output connection point of an [[OP Class#Connection|operator]].  There are two types of connections:  those between Components, and those between regular operators.

Connections between regular operators can be accessed through the [[OP Class#Connection|OP.inputConnectors]] and [[OP Class#Connection|OP.outputConnectors]] members. These are the connectors on the left and right sides of [[Operator|Operators]].

Connections between components can be accessed through the [[COMP Class#Connection|COMP.inputCOMPConnectors]] and [[COMP Class|COMP.outputCOMPConnectors]] members. These are the connectors on the top and bottom of [[Component]] operators"""
	index : int
	"""The numeric index of this connector."""
	isInput : bool
	"""True when the connector is an input."""
	isOutput : bool
	"""True when the connector is an output."""
	inOP : OP
	"""Will return any input operators (e.g. [[inSOP Class|inSOP]], [[inCHOP Class|inCHOP]]) associated with this connector.  This only applies to regular operator connections attached to components."""
	outOP : OP
	"""Will return any output operators (e.g. [[outSOP Class|outSOP]], [[outCHOP Class|outCHOP]]) associated with this connector.  This only applies to regular operator connections attached to components."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	connections : list
	"""The list of [[Connector Class|connector objects]] connected to this object."""
	description : str
	"""A description for this connection. Example: 'Color Image'."""
	par : parameter.Connector
	"""Parameters of parameter.Connector"""
	def connect(self, target) -> None: 
		"""Wire this connector to a target location. The target may be an [[OP Class|operator]] or another connector.

When the connector is an input, its connection is replaced with the target.

When the connector is an output, a new connection is appended to the target.

* target - The OP or connector you want to connect to.

```python


# connect noise1 to lag1

op('noise1').outputConnectors[0].connect(op('lag1'))



# connect choptotop1 to 2nd input of displace1

op('choptotop1').outputConnectors[0].connect(op('displace1').inputConnectors[1])



# connect geo1 to geo2, two equivalent methods:

op('geo1').outputCOMPConnectors[0].connect(op('geo2'))

op('geo2').inputCOMPConnectors[0].connect(op('geo1'))


```"""
		pass
	def disconnect(self, ) -> None: 
		"""Disconnect this connector.

```python


op('lag1').inputConnectors[0].disconnect()

op('lag1').outputConnectors[0].disconnect()



# disconnect geo2 from geo1, two equivalent methods

op('geo1').outputCOMPConnectors[0].disconnect()

op('geo2').inputCOMPConnectors[0].disconnect()


```"""
		pass
	pass


class Colors():
	"""The Colors Class describes the application colors.  It can be accessed from the global [[UI Class|ui]] object."""
	par : parameter.Colors
	"""Parameters of parameter.Colors"""
	def resetToDefaults(self, ) -> None: 
		"""Set the colors to their default values."""
		pass
	def len(self, Colors) -> int: 
		"""Returns the total color options.

```python


a = len(ui.colors)


```"""
		pass
	def [<color option name>] -> any: 
		"""Get or set specific color option, given a string key.

```python


n = ui.colors['default.bg']

ui.colors['default.bg'] = (1,0,0)


```"""
		pass
	def Iterator -> str: 
		"""Iterate over each color option name.

```python


for n in ui.colors:

        print(n)

        ui.colors[n] = myColorsList[n]


```"""
		pass
	pass


class Color():
	"""The color class holds a single 4 component color (R, G, B, A).

```python


v = tdu.Color() # starts as (0, 0, 0, 1)

v2 = tdu.Color(0, 0, 1, 1)

values = [0, 1, 0, 1]

v3 = tdu.Color(values)

green = v3[1] # access individual elements by index. Same as v3.g


```
"""
	r : float
	"""Gets or sets the red component of the color."""
	g : float
	"""Gets or sets the green component of the color."""
	b : float
	"""Gets or sets the blue component of the color."""
	a : float
	"""Gets or sets the alpha component of the color."""
	par : parameter.Color
	"""Parameters of parameter.Color"""
	def [index] -> float: 
		"""Sample values may be accessed from a Color using the [] subscript operator."""
		pass
	def copy(self, ) -> Color: 
		"""Returns a new color that is a copy of the color."""
		pass
	pass


class InputPoint():
	"""A Input Point is a special case of a Point object, only available in the [[Point SOP|Point SOP's]] parameters."""
	color : Color
	"""The color for this point. This is different from the Cd attribute, since it can come from a Vertex if there is no color on the inputPoint itself."""
	normP : Position
	"""The normalized position of this point within the bounding box of the SOP. Will always be in the range [0,1]. Expressed as tdu.Position object."""
	normal : Vector
	"""The normal for this point. This is different from the N attribute, since it can come from a Vertex or from the destination point, if there is no normal on the inputPoint itself."""
	sopCenter : Position
	"""Get the barycentric coordinate of the geometry the inputPoint is a part of. This is faster than other methods to get the center of a SOP's geometry due to internal optimizations. It is expressed as a tdu.Position."""
	par : parameter.InputPoint
	"""Parameters of parameter.InputPoint"""
	pass


class Channel():
	"""A Channel object describes a single [[Channel|channel]] from a [[CHOP]].  The [[CHOP Class]] provides many ways of accessing its individual channels.

See [[Working with CHOPs in Python]] for more examples of how to use this class."""
	valid : bool
	"""True if the referenced chanel value currently exists, False if it has been deleted."""
	index : int
	"""The numeric index of the channel."""
	name : str
	"""The name of the channel."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	exports : list
	"""The (possibly empty) list of [[Par Class|parameters]] this channel currently exports to."""
	vals : list
	"""Get or set the full list of [[Channel Class|Channel]] values. Modifying [[Channel Class|Channel]] values can only be done in Python within a [[scriptCHOP Class|Script CHOP]]."""
	par : parameter.Channel
	"""Parameters of parameter.Channel"""
	def [index] -> float: 
		"""Sample values may be easily accessed from a Channel using the [] subscript operator.

* index - Must be an numeric sample index. Wildcards are not supported.

To get the third sample from the channel, assuming the channel has 3 or more samples:

```python


n = op('pattern1')

c = n['chan1'][2] # the third sample

l = len(n['chan2']) # the total number of samples in the channel


```"""
		pass
	def eval(self, index) -> float: 
		"""Evaluate the channel at the specified index sample index. If no index is given, the current index based on the current time is used.

* index - (Optional) The sample index to evaluate at."""
		pass
	def evalFrame(self, frame) -> float: 
		"""Evaluate the channel at the specified frame. If no frame is given, the current frame is used.

* frame  - (Optional) The frame to evaluate at."""
		pass
	def evalSeconds(self, secs) -> float: 
		"""Evaluate the channel at the specified seconds. If no time is given, the current time is used.

* secs - (Optional) The time in seconds to evaluate at."""
		pass
	def numpyArray(self, ) -> any: 
		"""Returns this channels data as a NumPy array with a length equal to the track length."""
		pass
	def destroy(self, ) -> None: 
		"""Destroy and remove the actual Channel this object refers to. This operation is only valid when the channel belongs to a [[scriptCHOP Class| Script CHOP]] or [[oscinCHOP Class|OSC In CHOP]] .

Note: after this call, other existing Channel objects in this CHOP may no longer be valid."""
		pass
	def average(self, ) -> float: 
		"""Returns the average value of all the channel samples."""
		pass
	def min(self, ) -> float: 
		"""Returns the minimum value of all the channel samples."""
		pass
	def max(self, ) -> float: 
		"""Returns the maximum value of all the channel samples."""
		pass
	def copyNumpyArray(self, numpyArray) -> None: 
		"""Copies the contents of the numpyArray into the Channel sample values.

*  numpyArray - The NumPy Array to copy. Must be shape(n), where n is the sample length of the CHOP. The data type must be float32. Modifying Channel values can only be done in Python within a [[Script CHOP]]."""
		pass
	pass


class Cell():
	"""The [[Cell Class]] describes the contents of a single cell from a [[DAT]] operator table.

The [[DAT Class]] offers many ways of accessing its individual cells.

[[DAT]] cells are always internally stored as strings, but may be accessed as numeric values.



'''IMPORTANT''':  ```op('table1')[1,2]</code> is this python cell object which usually gets converted for you to the string in the cell. More safely use <code>op('table1')[1,2].val``` which always gives you the string."""
	valid : bool
	"""True if the referenced cell currently exists, False if it has been deleted."""
	row : int
	"""The numeric row of the cell."""
	col : int
	"""The numeric column of the cell."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	val : value
	"""Get or set the cell contents, which are always stored as a string value."""
	par : parameter.Cell
	"""Parameters of parameter.Cell"""
	def run(self, endFrame=False, fromOP=None, asParameter=False, group=None, delayFrames=0, delayMilliSeconds=0, delayRef=me, arg1, arg2, *args) -> any: 
		"""[[Run Class|Run]] the contents of the cell as a script, returning a Run object which can be used to optionally modify its execution.

* endFrame - (Keyword, Optional) If set to True, the execution will be delayed until the end of the current frame.

* fromOP - (Keyword, Optional) Specifies an optional [[OP Class|operator]] from which the execution will be run relative to.

* asParameter - (Keyword, Optional) When fromOP used, run relative to a parameter of fromOP.

* group - (Keyword, Optional) Can be used to specify a group label string. This label can then be used with the [[Runs Class|td.runs]] object to modify its execution.

* delayFrames - (Keyword, Optional) Can be used to delay the execution a specific amount of frames.

* delayMilliSeconds - (Keyword, Optional) Can be used to delay the execution a specific amount of milliseconds.  This value is rounded to the nearest frame.

* delayRef - (Keyword, Optional) Specifies an optional [[OP Class|operator]] from which the delay time is derived.

* arg - (Optional) Arguments that will be made available to the script in a local tuple named args."""
		pass
	def offset(self, r, c) -> any: 
		"""The cell offset to this cell by the specified amount, or None.

* r - The number of rows from the cell.  Positive values count down, while negative values count up.

* c - The number of columns from the cell.  Positive values count right, while negative values count left.

```python


c = op('table1')['March', 'Sales']

d = c.offset(-1, 2)  # one row up, two columns right of cell C


```"""
		pass
	pass


class Camera():
	"""Helper class that maintains a 3D position and orientation for a camera and provides multiple methods for manipulating the camera's position and direction. This class is used for the [[Palette:camera|viewportCamera]] palette component."""
	dir : tdu.Position
	"""Get or set the direction of the camera as a vector that points towards the target. Up is considered to be (0,1,0)."""
	pivot : tdu.Position
	"""Get or set the 3D point in space where the camera will pivot around or towards."""
	position : tdu.Position
	"""Get or set the 3D point in space where the camera is located."""
	par : parameter.Camera
	"""Parameters of parameter.Camera"""
	def blendCamera(self, targetCamera, blendFactor) -> any: 
		"""Returns a camera that is blended with the given camera using the blendFactor. The camera position is blended using linear interpolation, while the rotation is blended using spherical linear interpolation.

*  targetCamera - A second camera that is the blend target.

*  blendfactor - A blend value between 0 and 1.'"""
		pass
	def dolly(self, ) -> None: 
		"""Move the camera away or towards the pivot point."""
		pass
	def frameBounds(self, ) -> any: 
		"""Set the camera to frame the given bounding box. Returns the width of the framed scene that can be used when setting up orthographic projections."""
		pass
	def look(self, ) -> None: 
		"""Pivot the camera around its position."""
		pass
	def move3D(self, ) -> None: 
		"""Move the camera using data from a 3D mouse."""
		pass
	def pan(self, ) -> None: 
		"""Pan the camera in a 2D plane facing the pivot point."""
		pass
	def setTransform(self, ) -> None: 
		"""Set the camera view matrix."""
		pass
	def track(self, ) -> None: 
		"""Move the camera up/down in the Y-Axis or left/right."""
		pass
	def transform(self, ) -> None: 
		"""Get the camera view matrix."""
		pass
	def tumble(self, ) -> None: 
		"""Rotate the camera around the pivot point."""
		pass
	def walk(self, ) -> None: 
		"""Move the camera forward/back along in the ZX plane and rotate around its position."""
		pass
	pass


class Bounds():
	"""Bounds(min, max, center, size)"""
	par : parameter.Bounds
	"""Parameters of parameter.Bounds"""
	pass


class Body():
	"""The Body Class describes the contents of a single body within an [[Actor COMP]].

The [[Actor COMP]] has a list of all its bodies."""
	index : int
	"""The index of this Body in its [[Actor COMP]] (owner)."""
	owner : OP
	"""The [[Actor COMP]] to which this body belongs."""
	rotate : tdu.Vector
	"""Get or set the body's rotation in world space."""
	translate : tdu.Position
	"""Get or set the body's translation in world space."""
	angularVelocity : tdu.Vector
	"""Get or set the body's angular velocity."""
	linearVelocity : tdu.Vector
	"""Get or set the body's linear velocity."""
	par : parameter.Body
	"""Parameters of parameter.Body"""
	def applyImpulseForce(self, force, relPos=None) -> None: 
		"""Applies impulse force to a body in a Bullet simulation.

*  force - The impulse force to apply to the body.

*  relPos (Keyword, Optional) - If specified, applies the force at the relative position, otherwise applied at (0,0,0)."""
		pass
	def applyTorque(self, torque) -> None: 
		"""Applies torque to a body in a Bullet simulation. The torque will only be applied for a single frame.

* torque - The torque to apply to the body this frame."""
		pass
	def applyImpulseTorque(self, torque) -> None: 
		"""Applies impulse torque to a body in a Bullet simulation.

* torque - The impulse torque to apply to the body."""
		pass
	def applyForce(self, force, relPos=None) -> None: 
		"""Applies force to a body in a Bullet simulation. The force will only be applied for a single frame.

* force - The force to apply to the body this frame.

* relPos (Keyword, Optional) - If specified, applies the force at the relative position, otherwise applied at (0,0,0)."""
		pass
	pass


class Bodies():
	"""The Bodies Class describes the set of all [[Body Class|Bodies]] in an [[Actor COMP|Actor COMP]] (Actor COMPs are used by the [[Bullet Solver COMP]] and [[Nvidia Flex Solver COMP]]). The Bodies object is accessed via its Actor COMP and is used much like a Python list.

```python


bodies = op('bsolver1/actor1').bodies	# get the Bodies object

print(len(bodies))						# number of Bodies 

print(bodies[0])						# first Body in the list

for b in bodies:

	print(b)							# print all Bodies


```
"""
	par : parameter.Bodies
	"""Parameters of parameter.Bodies"""
	pass


class Bezier():
	"""A Bezier describes an instance of a single geometry Bezier primitive (containing a set of connected Bezier curves). It is an instance of a [[Prim Class]].

It can be created from either a [[modelSOP Class|Model SOP]] or [[scriptSOP Class|Script SOP]].

Each curve is described by a set of segments, where each segment is a list of [[Vertex Class|vertices]]. The first and last vertex of each segment is an anchor position, while its neighboring vertices describe tangent handles.



The members and methods below allow modification of the Bezier in a modelling context, however the Bezier can also be modified by direction manipulation of its vertices.  See [[Prim Class]] for more details."""
	anchors : list
	"""Returns the list of anchor [[Vertex Class|vertices]]."""
	basis : list
	"""Return the bezier basis as a list of float values."""
	closed : bool
	"""Get or set whether the curve is closed or open."""
	order : float
	"""Return the bezier order. The order is one more than the degree."""
	segments : list
	"""Returns a list of segments, where each segment is a list of [[Vertex Class|vertices]]."""
	tangents : list
	"""Returns the tangents as a list of [[Vertex Class|vertex]] pairs."""
	par : parameter.Bezier
	"""Parameters of parameter.Bezier"""
	def insertAnchor(self, u) -> Vertex: 
		"""inserts anchor at given position (u from 0..1) and returns anchor vertex."""
		pass
	def updateAnchor(self, anchorIndex, targetPosition, tangents=True) -> any: 
		"""Modify the anchor vertex to the new [[Position Class|position]]. If tangents is True, modify neighboring tangent vertices as well. Returns resulting position."""
		pass
	def appendAnchor(self, targetPosition, preserveShape=True) -> Vertex: 
		"""Appends a set of vertices, creating a new segment on the curve, ending with the targetPosition.

Returns final anchor vertex.

* preserveShape - (Keyword, Optional) Specifies whether the new tangent will align with the previous segment or not."""
		pass
	def updateTangent(self, tangentIndex, targetPosition, rotate=True, scale=True, rotateLock=True, scaleLock=True) -> any: 
		"""Modify the vertex vertex to the new [[Position Class|position]], constraining either rotation or scale. Locked controls matching tangent. Returns resulting position."""
		pass
	def deleteAnchor(self, anchorIndex) -> None: 
		"""Deletes the anchor and its neighbouring tangents."""
		pass
	pass


class NotSet():
	""""""
	par : parameter.NotSet
	"""Parameters of parameter.NotSet"""
	pass


class Attributes():
	"""An Attributes object describes a set of [[Prim Class|Prim]] Class, [[Point Class|Point]] Class, or [[Vertex Class]] [[Attribute|attributes]], contained within a [[SOP Class|SOP]]."""
	owner : any
	"""The [[OP Class|OP]] to which this object belongs."""
	par : parameter.Attributes
	"""Parameters of parameter.Attributes"""
	def [name] -> Attribute: 
		"""[[Attribute Class|Attributes]] can be accessed using the [] subscript operator.

* name - The name of the attribute.

```python


attribs = scriptOP.pointAttribs # get the Attributes object

normals = attribs['N']


```"""
		pass
	def create(self, name, default) -> Attribute: 
		"""Create a new [[Attribute Class|Attribute]].

* name - The name of the attribute.

* default - (Optional) Specify default values for custom attributes.  For standard attributes, default values are implied.



Standard attributes are: N (normal), uv (texture), T (tangent), v (velocity), Cd (diffuse color).

```python


# create a Normal attribute with implied defaults.

n = scriptOP.pointAttribs.create('N')



# set the X component of the first point's Normal attribute.

scriptOp.points[0].N[0] = 0.3



# Create a Vertex Attribute called custom1 with defaults set to (0.0, 0.0)

n = scriptOP.vertexAttribs.create('custom1', (0.0, 0.0) )



# Create a Primitive Attribute called custom2 defaulting to 1

n = scriptOP.primAttribs.create('custom2', 1 )


```"""
		pass
	pass


class AttributeData():
	"""An AttributeData contains specific geometric [[Attribute]] values, associated with a [[Prim Class]], [[Point Class]], or [[Vertex Class]].  Each value of the attribute must be of the same type, and can be one of float, string or integer.  For example, a point or vertex normal attribute data, consists of 3 float values."""
	owner : op
	"""The [[OP Class|OP]] to which this object belongs."""
	val : value
	"""The set of values contained within this object.  Dependent on the type of attribute, it may return a float, integer, string, tuple, [[Position Class|Position]], or [[Vector Class|Vector]].  For example Normal attribute data is expressed as a [[Vector Class|Vector]], while [[Position Class|Position]] attribute data is expressed as a Position."""
	par : parameter.AttributeData
	"""Parameters of parameter.AttributeData"""
	pass


class Attribute():
	"""An [[Attribute]] describes a general geometric Attribute, associated with a [[Prim Class]], [[Point Class]], or [[Vertex Class]].

Specific values for each Prim, Point or Vertex are described with the [[AttributeData Class]].

Lists of attributes for the [[SOP Class|SOP]] are described with the [[Attributes Class]]."""
	owner : OP
	"""The [[OP Class|OP]] to which this object belongs."""
	name : str
	"""The name of this attribute."""
	size : int
	"""The number of values associated with this attribute. For example, a normal attribute has a size of 3."""
	type : type object
	"""The type associated with this attribute: float, integer or string."""
	default : value
	"""The default values associated with this attribute. Dependent on the type of attribute, it may return a float, integer, string, tuple, [[Position Class|Position]], or [[Vector Class|Vector]]."""
	par : parameter.Attribute
	"""Parameters of parameter.Attribute"""
	def destroy(self, ) -> None: 
		"""Destroy the attribute referenced by this object.

```python


n = scriptOP.pointAttribs['N'].destroy()


```"""
		pass
	pass


class ArcBall():
	"""Encapsulates many aspects of 3D viewer interaction. Rotation via arcball, translation and scale.

```python


a = tdu.ArcBall(forCamera=False)


```
"""
	par : parameter.ArcBall
	"""Parameters of parameter.ArcBall"""
	def beginPan(self, u, v) -> None: 
		"""Begin a pan at at the given u and v.

```python


m.beginPan(.1, .2)


```"""
		pass
	def beginRotate(self, u, v) -> None: 
		"""Begin an arcball rotation at the given u and v.

```python


m.beginRotate(.1, .2)


```"""
		pass
	def beginDolly(self, u, v) -> None: 
		"""Begin a dolly at at the given u and v.

```python


m.beginDolly(.1, .2)


```"""
		pass
	def pan(self, u, v) -> None: 
		"""Pan the view by the given x and y.

```python


m.pan(.1, .2)


```"""
		pass
	def panTo(self, u, v, scale=1.0) -> None: 
		"""Pan from the u,v given in the last call to beginPan() to the given u and v, applying a scale as well to the pan amount.

* scale - (Keyword, Optional) Scale the operation by this amount.

```python


m.panTo(.1, .2)


```"""
		pass
	def rotateTo(self, u, v, scale=1.0) -> None: 
		"""Rotates the arcball to the given u and v position.

* scale - (Keyword, Optional) Scale the operation by this amount.

```python


m.rotateTo(.1, .2)


```"""
		pass
	def dolly(self, z) -> None: 
		"""Dolly the view by the given z value.

```python


m.dolly(.3)


```"""
		pass
	def dollyTo(self, u, v, scale=1.0) -> None: 
		"""Dolly from the u,v given in the last call to beginDolly() to the given u and v, applying a scale as well to the dolly amount.(Keyword, Optional)

* scale - Scale the operation by this amount.

```python


m.dollyTo(.1, .2)


```"""
		pass
	def transform(self, ) -> any: 
		"""Gets the current transform [[Matrix Class|matrix]] for the arcball.

```python


m.transform()


```"""
		pass
	def setTransform(self, matrix) -> None: 
		"""Sets the current transform matrix for the arcball. Scales in the given matrix will be ignored.

```python


m.setTransform(m)


```"""
		pass
	def identity(self, ) -> None: 
		"""Resets all values of the ArcBall to the default state.

```python


m.identity()


```"""
		pass
	pass


class App():
	"""This class contains specific application details, such as its version and installation folders. It can be accessed with the app object, found in the automatically imported [[td Module|td module]].



'''NOTE:''' See also [[Variables]] and Dialogs -> Variables where more built-in paths and strings are available via expressions in the form ```var('DESKTOP')</code>, <code>var('MYDOCUMENTS')</code> and <code>var('TOENAME')```."""
	architecture : str
	"""The architecture of the compile.  Generally 32 or 64 bit."""
	binFolder : str
	"""Installation folder containing the binaries."""
	build : str
	"""Application build number."""
	compileDate : tuple(year, month, day)
	"""The date the application was compiled, expressed as a tuple (year, month, day)."""
	configFolder : str
	"""Installation folder containing configuration files."""
	desktopFolder : str
	"""Current user's desktop folder."""
	enableOptimizedExprs : bool
	"""Get or set if Python expression optimization is enabled. Defaults to True every time TouchDesigner starts."""
	experimental : bool
	"""Returns true if the App is an experimental build, false otherwise."""
	installFolder : str
	"""Main installation folder."""
	launchTime : float
	"""Total time required to launch and begin playing the toe file, measured in seconds."""
	logExtensionCompiles : bool
	"""Get or set if extra messages for starting and ending compiling extensions is sent to the textport. Additional error stack will be printed if compilation fails.  Defaults to False every time TouchDesigner starts."""
	osName : str
	"""The operating system name."""
	osVersion : str
	"""The operating system version."""
	power : bool
	"""Get or set the overall processing state of the process. When True, processing is enabled.  When False processing is halted. This is identical to pressing the power button on the main interface. This has a greater effect than simply pausing or stopping the playbar.

```python


app.power = False #turn off the power button.


```
"""
	preferencesFolder : str
	"""Folder where the preferences file is located."""
	product : str
	"""Type of executable the project is running under. Values are 'TouchDesigner', 'TouchPlayer' or 'TouchEngine'."""
	recentFiles : list
	"""Get or set the list of most recently saved or loaded files."""
	samplesFolder : str
	"""Installation folder containing configuration files."""
	paletteFolder : str
	"""Installation folder containing palette files."""
	userPaletteFolder : str
	"""Folder where custom user palettes are located."""
	version : str
	"""Application version number."""
	windowColorBits : int
	"""The number of color bits per color channel the TouchDesigner window is running at. By default this will be 8-bits per channel, but can be increased to 10-bits by settings env var TOUCH_10_BIT_COLOR=1. Only works on displays that support 10-bit color."""
	par : parameter.App
	"""Parameters of parameter.App"""
	def addNonCommercialLimit(self, password) -> None: 
		"""Limits the application to operate at non-commercial license level. Multiple calls can be made, but each can be undone with a  matching removeNonCommercialLimit(password).  If the password is blank the operation cannot be undone. (See also [[Licenses Class|licenses.disablePro]]) member.

* password - (Keyword, Optional) Password to later remove the restriction.

```python


app.addNonCommercialLimit('secret123')  #undoable with password

app.addNonCommercialLimit()  #permanent during length of session.


```"""
		pass
	def removeNonCommercialLimit(self, password) -> bool: 
		"""Removes the restriction previously added. Returns True if successful.

* password - (Keyword) Password previously used when restriction added.

```python


app.removeNonCommercialLimit('secret123')


```"""
		pass
	def addResolutionLimit(self, x,y password) -> None: 
		"""Limits all textures to the specified amount. Multiple calls can be made, but each can be undone with a  matching removeResolutionLimit(password).  The final resolution limit will be the minimum of all calls. If the password is blank the operation cannot be undone.

* x - Width of maximum texture resolution, measured in pixels.

* y - Height of maximum texture resolution, measured in pixels.

* password - (Keyword, Optional) Password to later remove the restriction.

```python


app.addResolutionLimit(600, 480, 'secret123')  #undoable with password

app.addResolutionLimit()  #permanent during length of session.


```"""
		pass
	def removeResolutionLimit(self, password) -> bool: 
		"""Removes the restriction previously added. Returns True if successful.

* password - (Keyword) Password previously used when restriction added.

```python


app.removeResolutionLimit('secret123')


```"""
		pass
	pass


class Actors():
	"""The Actors Class describes the set of all [[Actor COMP|Actor COMPs]] used by the [[Bullet Solver COMP]] and [[Nvidia Flex Solver COMP]]. It can be accessed with a Bullet Solver COMP. It can be accessed much like a Python list.

```python


actors = op('bsolver1').actors	# get the Actors object

print(len(actors))				# number of Actors 

print(actors[0])				# first Actor component in the list

for a in actors:

	print(a)					# print all Actors


```
"""
	par : parameter.Actors
	"""Parameters of parameter.Actors"""
	pass


class AbsTime():
	"""This class contains information on the '[[Absolute Time|absolute time]]', the time TouchDesigner has been running since the process started.  It can be accessed with the abstime object, found in the automatically imported [[td Module|td module]]. It is paused only with the power on/off button at the top of the UI, or with the power() method in the [[td Module|td module]]. Absolute time is the same for all nodes and is not affected by the pausing any component's timeline. See  [http://en.wikipedia.org/wiki/Absolute_time_and_space absolute time]."""
	frame : float
	"""Absolute total number of frames played since the application started.  Paused only with the power On/Off or with power()

```python


Example: absTime.frame

Example: tdu.rand(absTime.frame + .1) # a unique random number that is consistent across all nodes, changing every frame


```
"""
	seconds : float
	"""Absolute total seconds played since the application started. Paused only with the power On/Off or with power()."""
	step : float
	"""Number of absolute frames elapsed between start of previous and current frame. When this value is greater than 1, the system is dropping frames."""
	stepSeconds : float
	"""Absolute time elapsed between start of previous and current frame."""
	par : parameter.AbsTime
	"""Parameters of parameter.AbsTime"""
	pass


class addSOP(SOP,OP):
	""""""
	par : parameter.addSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.addSOP & parameter.SOP & parameter.OP"""
	pass


class addTOP(TOP,OP):
	""""""
	par : parameter.addTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.addTOP & parameter.TOP & parameter.OP"""
	pass


class alembicSOP(SOP,OP):
	""""""
	par : parameter.alembicSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.alembicSOP & parameter.SOP & parameter.OP"""
	pass


class alignSOP(SOP,OP):
	""""""
	par : parameter.alignSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.alignSOP & parameter.SOP & parameter.OP"""
	pass


class ambientlightCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.ambientlightCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.ambientlightCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class analyzeCHOP(CHOP,OP):
	""""""
	par : parameter.analyzeCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.analyzeCHOP & parameter.CHOP & parameter.OP"""
	pass


class analyzeTOP(TOP,OP):
	""""""
	par : parameter.analyzeTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.analyzeTOP & parameter.TOP & parameter.OP"""
	pass


class angleCHOP(CHOP,OP):
	""""""
	par : parameter.angleCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.angleCHOP & parameter.CHOP & parameter.OP"""
	pass


class animationCOMP(COMP,OP):
	""""""
	par : parameter.animationCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.animationCOMP & parameter.COMP & parameter.OP"""
	def setKeyframe(self, position, channel='*', value=None, function=None) -> None: 
		"""Add or set a keyframe in an animation channel.

* position - The position along the x-axis of the animation channel.

* channel - (Optional) The channel to modify. Wildcards and patterns are supported. By default all channels are modified.

* value - (Keyword, Optional) The channel value at the keyframe.  If not specified, and no keyframe exists at that location, one is added such that the shape of the channel is preserved.

* function - (Keyword, Optional) The keyframe interpolation function."""
		pass
	def deleteKeyframe(self, position, channel='*', value=None, function=None) -> None: 
		"""Remove a keyframe from an animation channel.

* position - The position along the x-axis of the animation channel.

* channel - (Optional) The channel to modify. Wildcards and patterns are supported. By default all channels are modified.

```python


n = op('animation1')

n.deleteKeyframe(50) # remove keyframe on all channels

n.deleteKeyframe(75, channel='tz') # modify specific keyframe


```"""
		pass
	pass


class antialiasTOP(TOP,OP):
	""""""
	par : parameter.antialiasTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.antialiasTOP & parameter.TOP & parameter.OP"""
	pass


class armSOP(SOP,OP):
	""""""
	par : parameter.armSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.armSOP & parameter.SOP & parameter.OP"""
	pass


class artnetDAT(DAT,OP):
	""""""
	par : parameter.artnetDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.artnetDAT & parameter.DAT & parameter.OP"""
	pass


class attributeCHOP(CHOP,OP):
	""""""
	par : parameter.attributeCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.attributeCHOP & parameter.CHOP & parameter.OP"""
	pass


class attributecreateSOP(SOP,OP):
	""""""
	par : parameter.attributecreateSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.attributecreateSOP & parameter.SOP & parameter.OP"""
	pass


class attributeSOP(SOP,OP):
	""""""
	par : parameter.attributeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.attributeSOP & parameter.SOP & parameter.OP"""
	pass


class audiobandeqCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.audiobandeqCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiobandeqCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiodeviceinCHOP(CHOP,OP):
	""""""
	par : parameter.audiodeviceinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiodeviceinCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiodeviceoutCHOP(CHOP,OP):
	""""""
	par : parameter.audiodeviceoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiodeviceoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiodynamicsCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.audiodynamicsCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiodynamicsCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiofileinCHOP(CHOP,OP):
	""""""
	par : parameter.audiofileinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiofileinCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiofilterCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.audiofilterCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiofilterCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiomovieCHOP(CHOP,OP):
	""""""
	hasAudio : bool
	"""True if the movie has audio."""
	playbackRate : float
	"""The current movie playback rate."""
	par : parameter.audiomovieCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiomovieCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiooscillatorCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.audiooscillatorCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiooscillatorCHOP & parameter.CHOP & parameter.OP"""
	pass


class audioparaeqCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.audioparaeqCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audioparaeqCHOP & parameter.CHOP & parameter.OP"""
	pass


class audioplayCHOP(CHOP,OP):
	""""""
	par : parameter.audioplayCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audioplayCHOP & parameter.CHOP & parameter.OP"""
	def play(self, index, start=True, loop=False,  delaySeconds=0.0, pan=None, rolloff=None, volume=None, fadeSeconds=0.0) -> None: 
		"""Trigger the playing of audio samples specified in an [[Audio Play CHOP]].

* index - (Optional) The index of the audio sample to play, or all if not specified.

* start - (Keyword, Optional) When True, will play from the beginning of the sample. When False, will play from current location.

* loop - (Keyword, Optional) When True, will loop the audio. When False, will play only once.

* delaySeconds - (Keyword, Optional) The number of seconds to delay before playing the audio sample.

* pan - (Keyword, Optional) Pan the audio:(0 = left, 1 = right), else use pan specified in CHOP.

* volume - (Keyword, Optional) Specify a new volume to play the audio, else use volume specified in CHOP.

* fadeSeconds - (Keyword, Optional) The number of seconds to fade to the specified volume."""
		pass
	def stop(self, index) -> None: 
		"""Stop the playing of audio samples specified in an [[Audio Play CHOP]].

* index - (Optional) The index of the audio sample to play, or all if not specified."""
		pass
	pass


class audiorenderCHOP(CHOP,OP):
	""""""
	par : parameter.audiorenderCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiorenderCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiospectrumCHOP(CHOP,OP):
	""""""
	par : parameter.audiospectrumCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiospectrumCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiostreaminCHOP(CHOP,OP):
	""""""
	par : parameter.audiostreaminCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiostreaminCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiostreamoutCHOP(CHOP,OP):
	""""""
	par : parameter.audiostreamoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiostreamoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class audiowebrenderCHOP(CHOP,OP):
	""""""
	par : parameter.audiowebrenderCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.audiowebrenderCHOP & parameter.CHOP & parameter.OP"""
	pass


class baseCOMP(COMP,OP):
	""""""
	par : parameter.baseCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.baseCOMP & parameter.COMP & parameter.OP"""
	pass


class basisSOP(SOP,OP):
	""""""
	par : parameter.basisSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.basisSOP & parameter.SOP & parameter.OP"""
	pass


class beatCHOP(CHOP,OP):
	""""""
	par : parameter.beatCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.beatCHOP & parameter.CHOP & parameter.OP"""
	pass


class blacktraxCHOP(CHOP,OP):
	""""""
	par : parameter.blacktraxCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.blacktraxCHOP & parameter.CHOP & parameter.OP"""
	pass


class blendCHOP(CHOP,OP):
	""""""
	par : parameter.blendCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.blendCHOP & parameter.CHOP & parameter.OP"""
	pass


class blendCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.blendCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.blendCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class blendSOP(SOP,OP):
	""""""
	par : parameter.blendSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.blendSOP & parameter.SOP & parameter.OP"""
	pass


class blobtrackTOP(TOP,OP):
	""""""
	par : parameter.blobtrackTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.blobtrackTOP & parameter.TOP & parameter.OP"""
	pass


class blurTOP(TOP,OP):
	""""""
	par : parameter.blurTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.blurTOP & parameter.TOP & parameter.OP"""
	pass


class boneCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.boneCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.boneCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class bonegroupSOP(SOP,OP):
	""""""
	par : parameter.bonegroupSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.bonegroupSOP & parameter.SOP & parameter.OP"""
	pass


class booleanSOP(SOP,OP):
	""""""
	par : parameter.booleanSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.booleanSOP & parameter.SOP & parameter.OP"""
	pass


class boxSOP(SOP,OP):
	""""""
	par : parameter.boxSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.boxSOP & parameter.SOP & parameter.OP"""
	pass


class bridgeSOP(SOP,OP):
	""""""
	par : parameter.bridgeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.bridgeSOP & parameter.SOP & parameter.OP"""
	pass


class buttonCOMP(PanelCOMP,COMP,OP):
	""""""
	par : parameter.buttonCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.buttonCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	def click(self, val, clickCount=1, force=False, left=False, middle=False, right=False) -> None: 
		"""Simulate a mouse click of a button panel.

* val - (Optional) If specified, the button state will retain that value.

* clickCount - (Keyword, Optional) Sets the number of clicks, for double clicking etc.

* force - (Keyword, Optional) Set to True to forces the panel click, even if its disabled.

* left,middle,right - (Keyword, Optional) Set to True to override the default mouse buttons used. When none are set, the left mouse button is pressed, and the other buttons released."""
		pass
	pass


class cacheselectTOP(TOP,OP):
	""""""
	par : parameter.cacheselectTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.cacheselectTOP & parameter.TOP & parameter.OP"""
	pass


class cacheSOP(SOP,OP):
	""""""
	par : parameter.cacheSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.cacheSOP & parameter.SOP & parameter.OP"""
	pass


class cacheTOP(TOP,OP):
	""""""
	par : parameter.cacheTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.cacheTOP & parameter.TOP & parameter.OP"""
	pass


class camerablendCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.camerablendCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.camerablendCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class cameraCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.cameraCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.cameraCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	def projectionInverse(self, x, y) -> any: 
		"""Returns the inverse projection matrix for the camera, given the X and Y aspect. In general these would be set to the width and height of your render.

* x - The horizontal aspect ratio.

* y - The vertical aspect ratio."""
		pass
	def projection(self, x, y) -> any: 
		"""Returns the projection matrix for the camera, given the X and Y aspect. In general these would be set to the width and height of your render.

* x - The horizontal aspect ratio.

* y - The vertical aspect ratio."""
		pass
	pass


class capSOP(SOP,OP):
	""""""
	par : parameter.capSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.capSOP & parameter.SOP & parameter.OP"""
	pass


class captureregionSOP(SOP,OP):
	""""""
	par : parameter.captureregionSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.captureregionSOP & parameter.SOP & parameter.OP"""
	pass


class captureSOP(SOP,OP):
	""""""
	par : parameter.captureSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.captureSOP & parameter.SOP & parameter.OP"""
	pass


class carveSOP(SOP,OP):
	""""""
	par : parameter.carveSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.carveSOP & parameter.SOP & parameter.OP"""
	pass


class channelmixTOP(TOP,OP):
	""""""
	par : parameter.channelmixTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.channelmixTOP & parameter.TOP & parameter.OP"""
	pass


class CHOP(OP):
	"""A [[CHOP]] describes a reference to a CHOP operator, containing a set of [[Channel|channels]] accessed with the [[Channel Class]]."""
	numChans : int
	"""The number of channels."""
	numSamples : int
	"""Get or set the number of samples (or indices) per channel. You can change the number of samples by setting this value, only in a [[scriptCHOP Class|scriptCHOP]]."""
	start : float
	"""Get or set the start index of the channels. This can be modified only when the CHOP is a [[scriptCHOP Class|scriptCHOP]]."""
	end : float
	"""Get or set the end index of the channels. This can be modified only when the CHOP is a [[scriptCHOP Class|scriptCHOP]]."""
	rate : float
	"""Get or set the sample rate of the CHOP. This can be modified only when the CHOP is a [[scriptCHOP Class|scriptCHOP]]."""
	isTimeSlice : bool
	"""Get or set the last cooked [[Time Slicing|Time Slice]] value. True if the CHOP last cooked as a Time Slice. This can be modified only when the CHOP is a [[scriptCHOP Class|scriptCHOP]]"""
	export : bool
	"""Get or set [[Export Flag]]."""
	exportChanges : int
	"""Number of times the export mapping information has changed."""
	isCHOP : bool
	"""True if the operator is a CHOP."""
	par : parameter.CHOP|parameter.OP
	"""Parameters of parameter.CHOP & parameter.OP"""
	def [nameOrIndex] -> Channel: 
		"""[[Channel Class|Channels]] may be easily accessed from a CHOP using the [] subscript operator.

* nameOrIndex - Must be an exact string name, or it may be a numeric channel index. Wildcards are not supported. Refer to the help on channels to see how to use the returned [[Channel Class|Channel]] object.```'python'


n = op('pattern1')

c = n[4]

c = n['chan2']


```
and to get the third sample from the channel, assuming the channel has 3 or more samples:```'python'


n = op('pattern1')

c = n['chan2'][2]


```"""
		pass
	def chan(self, nameOrIndex1, nameOrIndex2, *args, caseSensitive=True) -> any: 
		"""Returns the first [[Channel Class|Channel]] that matches the given name or index or None if none are found.

Multiple patterns may be specified which are all added to the search.

* nameOrIndex - May be a string name, possibly using [[Pattern Matching]], or it may be a numeric channel index.

* caseSensitive - (Optional) Specifies whether or not case sensitivity is used.

```'python'


n = op('pattern1')

c = n.chan(4)

c = n.chan('chan* ')

c = n.chan('chan3zall', caseSensitive=False)


```"""
		pass
	def chans(self, nameOrIndex1, nameOrIndex2, *args, caseSensitive=True) -> list: 
		"""Returns a (possibly empty) list of [[Channel Class|Channels]] that match that specified names or indices. Multiple names and indices may be provided.

* nameOrIndex - (Optional) One or more string names, possibly using [[Pattern Matching]], or numeric channel index. No arguments are passed, a list of all channels is returned.

* caseSensitive - (Optional) Specifies whether or not case sensitivity is used.

```'python'


n = op('pattern1')

newlist = n.chans() # get all channels in the CHOP

newlist = n.chans('a* ', 3,4,5, 'd* ')


```"""
		pass
	def numpyArray(self, ) -> any: 
		"""Returns all of the channels in this CHOP a 2D NumPy array with a width equal to the channel length (the number of samples) and a height equal to the number of channels. See [[numPy]]."""
		pass
	def convertToKeyframes(self, tolerance=0.1) -> animationCOMP: 
		"""Create an [[Animation COMP]] that contains a keyframed approximation of the CHOP's channels.

The resultant [[animationCOMP Class|animationCOMP]] is returned.

* tolerance - (Keyword, Optional) If this is not given, the default value is 0.1. It may be overridden for higher accuracy match between the source channels and the resulting keyframed channels."""
		pass
	def save(self, filepath, createFolders=False) -> any: 
		"""Saves the channel to the file system. Supported file formats are ```.clip, .bclip, .chan, .bchan</code> and <code>.aiff```.

Returns the file path used.

* filepath - (Optional) The path and filename to save to.

* createFolders - (Keyword, Optional) If True, it creates the not existent directories provided by the filepath.

```'python'


n = op('pattern1')

name = n.save()   #save in native format with default name

n.save('output.chan')  #ascii readable tab delimited format

n.save('output.aiff')  #supported audio format


```"""
		pass
	pass


class zedCHOP(CHOP,OP):
	""""""
	par : parameter.zedCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.zedCHOP & parameter.CHOP & parameter.OP"""
	pass


class waveCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.waveCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.waveCHOP & parameter.CHOP & parameter.OP"""
	pass


class warpCHOP(CHOP,OP):
	""""""
	par : parameter.warpCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.warpCHOP & parameter.CHOP & parameter.OP"""
	pass


class trimCHOP(CHOP,OP):
	""""""
	par : parameter.trimCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.trimCHOP & parameter.CHOP & parameter.OP"""
	pass


class triggerCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.triggerCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.triggerCHOP & parameter.CHOP & parameter.OP"""
	pass


class transformCHOP(CHOP,OP):
	""""""
	par : parameter.transformCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.transformCHOP & parameter.CHOP & parameter.OP"""
	pass


class trailCHOP(CHOP,OP):
	""""""
	par : parameter.trailCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.trailCHOP & parameter.CHOP & parameter.OP"""
	pass


class touchoutCHOP(CHOP,OP):
	""""""
	par : parameter.touchoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.touchoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class touchinCHOP(CHOP,OP):
	""""""
	par : parameter.touchinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.touchinCHOP & parameter.CHOP & parameter.OP"""
	pass


class toptoCHOP(CHOP,OP):
	""""""
	par : parameter.toptoCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.toptoCHOP & parameter.CHOP & parameter.OP"""
	pass


class timesliceCHOP(CHOP,OP):
	""""""
	par : parameter.timesliceCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.timesliceCHOP & parameter.CHOP & parameter.OP"""
	pass


class timerCHOP(CHOP,OP):
	""""""
	beginFrame : list
	"""Get a list of begin values in frames. 0-based."""
	beginSample : list
	"""Get a list of begin values in samples. 0-based."""
	beginSeconds : list
	"""Get a list of begin values in seconds."""
	cumulativeFrames : int
	"""Get the cumulative time expressed in frames. See ```.cumulativeSeconds```."""
	cumulativeSample : int
	"""Get the cumulative time expressed in samples. See ```.cumulativeSeconds```."""
	cumulativeSamples : int
	"""Get the cumulative time expressed in samples. See ```.cumulativeSeconds```."""
	cumulativeSeconds : float
	"""Get the cumulative time expressed in seconds. It counts from 0 when you Start. Unlike ```.runningSeconds```, it is slowed/sped by the Speed parameter, and paused by the Play parameter. It continues to increase if there is any looping, jumping or scrubbing around."""
	cumulativeTimecode : str
	"""Get the cumulative time as a timecode in the form 00:00:00.00. See ```.cumulativeSeconds```."""
	masterFrames : int
	"""Get or set the master time expressed in frames. 0-based. See ```.masterSeconds```."""
	masterFrame : int
	"""Get or set the master time expressed in frames. 0-based. See ```.masterSeconds```."""
	masterSamples : int
	"""Get or set the master time expressed in samples. See ```.masterSeconds```."""
	masterSample : int
	"""Get or set the master time expressed in samples. See ```.masterSeconds```."""
	masterSeconds : float
	"""Get or set the master time expressed in seconds. It counts from 0 when you Start, ```.masterSeconds</code> is slowed/sped by the Speed parameter, and paused by the Play parameter. It jumps to the appropriate time when you scrub. This is the main clock in the Timer CHOP and can be set directly using python (<code>OP.masterSeconds = ''val''</code>), or use the <code>.goTo()``` function which has more options. When multi-segments are specified to the Timer CHOP, it reflects the time as if you ran through the segments without interrupting it. If in any segment Cycle is on and Cycle Limit is off, it calculates as if the cycle runs only once."""
	masterFraction : float
	"""Get or set the master time expressed in fractional form. See ```.masterSeconds```."""
	masterTimecode : str
	"""Get or set the master time expressed as a timecode in the form 00:00:00.00. See ```.masterSeconds```."""
	cycle : float
	"""Get or set the cycle index of the current segment."""
	fraction : float
	"""Get the time index in fractional form, same as the ```timer_fraction``` channel. Used in the callbacks, it's more up-to-date to the current frame. (When using segments, it's the first segment)."""
	playingFrames : int
	"""Get the playing time expressed in frames. 0-based. See ```.playingSeconds```."""
	playingSample : int
	"""Get the playing time expressed in samples. See ```.playingSeconds```."""
	playingSamples : int
	"""Get the playing time expressed in samples. See ```.playingSeconds```."""
	playingSeconds : float
	"""Get the playing time expressed in seconds. It counts from 0 when you Start. it is unaffected by the Speed parameter, but unlike ```.runningSeconds```, it is paused by the Play parameter. It continues to increase if there is any looping, jumping or scrubbing around."""
	playingTimecode : str
	"""Get the playing time as a timecode in the form 00:00:00.00. See ```.playingSeconds```."""
	runningFraction : float
	"""Get the running time index expressed in fractional form. See ```.runningSeconds```. This will be an estimate as the actual length is approximated on start."""
	runningFrames : float
	"""Get the running time expressed in frames. 0-based. See ```.runningSeconds```."""
	runningFrame : float
	"""Get the running time expressed in frames. 0-based. See ```.runningSeconds```."""
	runningSamples : float
	"""Get the running time index expressed in samples. See ```.runningSeconds```."""
	runningSample : float
	"""Get the running time index expressed in samples. See ```.runningSeconds```."""
	runningSeconds : float
	"""Get the running time expressed in seconds. It keeps counting up after Start and is not affected by changing the Speed or pausing Play or scrubbing. It is basically the 'wall clock' after pressing Start. (You normally don't set the value, use ```.masterSeconds```.)  It doesn't reset to 0 until you Initialize or Start again."""
	runningTimecode : str
	"""Get the running time index as a timecode in the form 00:00:00.00. See ```.runningSeconds```."""
	runningLengthFrames : float
	"""Get the running length expressed in frames."""
	runningLengthSamples : float
	"""Get the running length expressed in samples."""
	runningLengthSeconds : float
	"""Get the running length expressed in seconds."""
	runningLengthTimecode : str
	"""Get the running length as a timecode in the form 00:00:00.00."""
	segment : float
	"""Get or set the segment index."""
	segments : list
	"""Get the list of segments."""
	par : parameter.timerCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.timerCHOP & parameter.CHOP & parameter.OP"""
	def goToNextSegment(self, ) -> None: 
		"""Jump to the next segment. Equivalent to pulsing the Go to Next Segment parameter on the Segments Page."""
		pass
	def goToCycleEnd(self, ) -> None: 
		"""Jump to the end of the current cycle. Equivalent to pulsing the Go to End of Cycle parameter on the Timer Page."""
		pass
	def goTo(self, segment=num, cycle=num, endOfCycle=True, seconds=num, frame=num, sample=num,  fraction=num) -> None: 
		"""Allows the user to jump to a different time index based on the arguments passed in. Only one unit of time (seconds, frame, sample, fraction) can be specified when calling this method. For example, including both seconds and frame will yield an error. If there are multiple segments, and only a unit of time is specified, the method will jump to the corresponding running time index. If either a segment index or a cycle index or both are specified along with a unit of time, the method will jump to the corresponding local time index. There are fifteen different combinations of arguments that the user can pass in. An example of how this method can be called is: timerop.goTo(segment=1, cycle=2, seconds=5, endOfCycle=True).

* segment - (Keyword, Optional) If specified, will jump to the indicated segment number (0 is first).

* cycle - (Keyword, Optional) If specified, will jump to the indicated cycle number (0 is first).

* endOfCycle - (Keyword, Optional) False by default. If specified as True, the goTo() function with the specified arguments will be called again at the end of the cycle, causing a jump only at that time to the specified location.

* seconds - (Keyword, Optional) If specified, will jump to the indicated time index. Cannot also specify frame, sample, or fraction.

* frame - (Keyword, Optional) If specified, will jump to the indicated time index. Cannot also specify seconds, sample, or fraction.

* sample - (Keyword, Optional) If specified, will jump to the indicated time index. Cannot also specify seconds, frame, or fraction.

* fraction - (Keyword, Optional) If specified, will jump to the indicated time index. Cannot also specify seconds, frame, or sample."""
		pass
	def goToPrevSegment(self, ) -> None: 
		"""Jump to the previous segment. Equivalent to pulsing the Go to Previous Segment parameter on the Segments Page."""
		pass
	def lastCycle(self, ) -> None: 
		"""Sets the current cycle to be the last cycle of the current segment. Equivalent to pulsing the Exit at End of Cycle parameter on the Timer Page."""
		pass
	pass


class timelineCHOP(CHOP,OP):
	""""""
	par : parameter.timelineCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.timelineCHOP & parameter.CHOP & parameter.OP"""
	pass


class tabletCHOP(CHOP,OP):
	""""""
	par : parameter.tabletCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.tabletCHOP & parameter.CHOP & parameter.OP"""
	pass


class syncoutCHOP(CHOP,OP):
	""""""
	par : parameter.syncoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.syncoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class syncinCHOP(CHOP,OP):
	""""""
	par : parameter.syncinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.syncinCHOP & parameter.CHOP & parameter.OP"""
	pass


class switchCHOP(CHOP,OP):
	""""""
	par : parameter.switchCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.switchCHOP & parameter.CHOP & parameter.OP"""
	pass


class stretchCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.stretchCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.stretchCHOP & parameter.CHOP & parameter.OP"""
	pass


class springCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.springCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.springCHOP & parameter.CHOP & parameter.OP"""
	pass


class spliceCHOP(CHOP,OP):
	""""""
	par : parameter.spliceCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.spliceCHOP & parameter.CHOP & parameter.OP"""
	pass


class speedCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.speedCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.speedCHOP & parameter.CHOP & parameter.OP"""
	pass


class sortCHOP(CHOP,OP):
	""""""
	par : parameter.sortCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.sortCHOP & parameter.CHOP & parameter.OP"""
	pass


class soptoCHOP(CHOP,OP):
	""""""
	par : parameter.soptoCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.soptoCHOP & parameter.CHOP & parameter.OP"""
	pass


class slopeCHOP(CHOP,OP):
	""""""
	par : parameter.slopeCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.slopeCHOP & parameter.CHOP & parameter.OP"""
	pass


class shuffleCHOP(CHOP,OP):
	""""""
	par : parameter.shuffleCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.shuffleCHOP & parameter.CHOP & parameter.OP"""
	pass


class shiftCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.shiftCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.shiftCHOP & parameter.CHOP & parameter.OP"""
	pass


class sharedmemoutCHOP(CHOP,OP):
	""""""
	par : parameter.sharedmemoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.sharedmemoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class sharedmeminCHOP(CHOP,OP):
	""""""
	par : parameter.sharedmeminCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.sharedmeminCHOP & parameter.CHOP & parameter.OP"""
	pass


class serialCHOP(CHOP,OP):
	""""""
	par : parameter.serialCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.serialCHOP & parameter.CHOP & parameter.OP"""
	pass


class sequencerCHOP(CHOP,OP):
	""""""
	par : parameter.sequencerCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.sequencerCHOP & parameter.CHOP & parameter.OP"""
	pass


class selectCHOP(CHOP,OP):
	""""""
	par : parameter.selectCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.selectCHOP & parameter.CHOP & parameter.OP"""
	pass


class scurveCHOP(CHOP,OP):
	""""""
	chanIndex : any
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.scurveCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.scurveCHOP & parameter.CHOP & parameter.OP"""
	pass


class scriptCHOP(CHOP,OP):
	""""""
	timeSliceDefault : bool
	"""Get the default [[Time Slice]] for the [[Script CHOP]]. Equal to the first input's ```isTimeSlice```."""
	par : parameter.scriptCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.scriptCHOP & parameter.CHOP & parameter.OP"""
	def copyNumpyArray(self, numpyArray, baseName='chan') -> None: 
		"""Copies the contents of the numpyArray into the CHOP.

* numpyArray - The NumPy Array to copy. Must be <syntaxhighlight lang=python, inline=true>shape(numChannels, numSamples)</syntaxhighlight>. The data type must be float32.

*  baseName - (Keyword, Optional) The base of all created channel names beginning with a suffix of 1. Example 'chan' creates 'chan1', 'chan2', etc."""
		pass
	def destroyCustomPars(self, ) -> any: 
		"""Remove all custom parameters from COMP."""
		pass
	def sortCustomPages(self, page1, page2, page3, *args) -> None: 
		"""Reorder custom parameter pages.



scriptOp.sortPages('Definition','Controls')"""
		pass
	def clear(self, ) -> None: 
		"""Remove all channels from the CHOP. The channel length, sample rate etc. remain unchanged."""
		pass
	def appendCustomPage(self, name) -> Page: 
		"""Add a new [[Page Class|page]] of custom parameters. See [[Page Class]] for more details.

```python


page = scriptOp.appendCustomPage('Custom1')

page.appendFloat('X1')


```"""
		pass
	def copy(self, chop) -> None: 
		"""Match all of this CHOPs channel data to the given [[CHOP]]. This includes sample rate, length, channel names and channel data.

* chop - The CHOP to copy. This should be a [[CHOP Class]] instance, not a path to the CHOP."""
		pass
	def appendChan(self, name) -> Channel: 
		"""Append a new channel to the CHOP. If no name is given the channel will be given a default but unique name.

* name - (Optional) The name to give the channel.

```python


c = n.appendChan()

c = n.appendChan('velocity')


```"""
		pass
	pass


class scanCHOP(CHOP,OP):
	""""""
	par : parameter.scanCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.scanCHOP & parameter.CHOP & parameter.OP"""
	pass


class resampleCHOP(CHOP,OP):
	""""""
	par : parameter.resampleCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.resampleCHOP & parameter.CHOP & parameter.OP"""
	pass


class replaceCHOP(CHOP,OP):
	""""""
	par : parameter.replaceCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.replaceCHOP & parameter.CHOP & parameter.OP"""
	pass


class reorderCHOP(CHOP,OP):
	""""""
	par : parameter.reorderCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.reorderCHOP & parameter.CHOP & parameter.OP"""
	pass


class renderpickCHOP(CHOP,OP):
	""""""
	pickedSOP : OP
	"""The [[SOP Class|SOP]] that was last picked."""
	par : parameter.renderpickCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.renderpickCHOP & parameter.CHOP & parameter.OP"""
	pass


class renameCHOP(CHOP,OP):
	""""""
	par : parameter.renameCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.renameCHOP & parameter.CHOP & parameter.OP"""
	pass


class recordCHOP(CHOP,OP):
	""""""
	par : parameter.recordCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.recordCHOP & parameter.CHOP & parameter.OP"""
	pass


class realsenseCHOP(CHOP,OP):
	""""""
	par : parameter.realsenseCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.realsenseCHOP & parameter.CHOP & parameter.OP"""
	pass


class pulseCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.pulseCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.pulseCHOP & parameter.CHOP & parameter.OP"""
	pass


class posistagenetCHOP(CHOP,OP):
	""""""
	par : parameter.posistagenetCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.posistagenetCHOP & parameter.CHOP & parameter.OP"""
	pass


class pipeoutCHOP(CHOP,OP):
	""""""
	par : parameter.pipeoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.pipeoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class pipeinCHOP(CHOP,OP):
	""""""
	par : parameter.pipeinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.pipeinCHOP & parameter.CHOP & parameter.OP"""
	pass


class performCHOP(CHOP,OP):
	""""""
	par : parameter.performCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.performCHOP & parameter.CHOP & parameter.OP"""
	pass


class patternCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""The index of the current [[Channel Class|channel]] being evaluated. For example, if Pattern generates three channels you can put ```[1, 3, 7][me.chanIndex]``` in the Amplitude parameter to customize the amplitude for each channel."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.patternCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.patternCHOP & parameter.CHOP & parameter.OP"""
	pass


class parameterCHOP(CHOP,OP):
	""""""
	par : parameter.parameterCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.parameterCHOP & parameter.CHOP & parameter.OP"""
	pass


class panelCHOP(CHOP,OP):
	""""""
	par : parameter.panelCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.panelCHOP & parameter.CHOP & parameter.OP"""
	pass


class overrideCHOP(CHOP,OP):
	""""""
	par : parameter.overrideCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.overrideCHOP & parameter.CHOP & parameter.OP"""
	pass


class outCHOP(CHOP,OP):
	""""""
	par : parameter.outCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.outCHOP & parameter.CHOP & parameter.OP"""
	pass


class oscoutCHOP(CHOP,OP):
	""""""
	par : parameter.oscoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.oscoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class oscinCHOP(CHOP,OP):
	""""""
	par : parameter.oscinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.oscinCHOP & parameter.CHOP & parameter.OP"""
	pass


class openvrCHOP(CHOP,OP):
	""""""
	par : parameter.openvrCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.openvrCHOP & parameter.CHOP & parameter.OP"""
	def triggerHapticPulse(self, controllerIndex, analogIndex, durationMilliseconds) -> None: 
		"""Triggers a haptic/vibration pulse on the given controller/analog index for the specified number of milliseconds.

* controllerIndex - 0 based controller index. Same order as the controllers are listed in the OpenVR CHOP.

* analogIndex - index of the analog button/pad. Currently only 0 is supported on Vive hardware.

* durationMilliSeconds - The length of the feedback in milliseconds. Anything equal to or above 4ms does not seem to work with current hardware."""
		pass
	pass


class oculusriftCHOP(CHOP,OP):
	""""""
	par : parameter.oculusriftCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.oculusriftCHOP & parameter.CHOP & parameter.OP"""
	pass


class oculusaudioCHOP(CHOP,OP):
	""""""
	par : parameter.oculusaudioCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.oculusaudioCHOP & parameter.CHOP & parameter.OP"""
	pass


class objectCHOP(CHOP,OP):
	""""""
	par : parameter.objectCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.objectCHOP & parameter.CHOP & parameter.OP"""
	pass


class nullCHOP(CHOP,OP):
	""""""
	par : parameter.nullCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.nullCHOP & parameter.CHOP & parameter.OP"""
	pass


class noiseCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.noiseCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.noiseCHOP & parameter.CHOP & parameter.OP"""
	pass


class natnetinCHOP(CHOP,OP):
	""""""
	par : parameter.natnetinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.natnetinCHOP & parameter.CHOP & parameter.OP"""
	pass


class mouseoutCHOP(CHOP,OP):
	""""""
	par : parameter.mouseoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.mouseoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class mouseinCHOP(CHOP,OP):
	""""""
	par : parameter.mouseinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.mouseinCHOP & parameter.CHOP & parameter.OP"""
	pass


class midioutCHOP(CHOP,OP):
	""""""
	par : parameter.midioutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.midioutCHOP & parameter.CHOP & parameter.OP"""
	def send(self, message1, message2, *args) -> None: 
		"""Send a sequence of bytes through this CHOP.

Messages can any combination of strings, byte arrays, or individual single-byte numeric values.

To serialize non-byte values (example floats or integers) there are several python modules to do this, such as pickle or struct.

```python


n.send(0xb0,0x2f,0x40) # Control Change : Channel 1, Index 48, Value 64


```
."""
		pass
	def sendBalance(self, channel, value) -> None: 
		"""Sends a Balance event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendBalance(1, 103)


```"""
		pass
	def sendNoteOn(self, channel, index, value) -> None: 
		"""Sends a Note On event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* index - The MIDI index/note.  Valid ranges are 0 to 127, or 1 to 128, dependent on the One Based Index parameter.

* value - (Optional) The MIDI note value.  Valid ranges are determined by the CHOP Note Normalize parameter. Maximum when not specified.

```python


n.sendNoteOn(1, 63)


```"""
		pass
	def sendPolyKeyPressure(self, channel, index, value) -> None: 
		"""Sends a Polyphonic Key Pressure event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* index - The MIDI index/note.  Valid ranges are 0 to 127, or 1 to 128, dependent on the One Based Index parameter.

* value - The MIDI pressure value.  Valid ranges are determined by the CHOP Note Normalize parameter.

```python


n.sendPolyKeyPressure(1, 63, 100)


```"""
		pass
	def sendPitchBend(self, channel, value) -> None: 
		"""Sends a Pitch Bend event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The pitch bend value.  Valid ranges are between 0 and 16384.

```python


n.sendPitchBend(1, 5000)


```"""
		pass
	def sendEffectsDepth(self, channel, index,value) -> None: 
		"""Sends a Effects Depth event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* index - Valid index ranges are 1 to 5.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendEffectsDepth(1,4,61)


```"""
		pass
	def sendMonoOn(self, channel,value) -> None: 
		"""Sends a Mono On/Poly Off event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendMonoOn(1,57)


```"""
		pass
	def panic(self, ) -> None: 
		"""Sends a volume off event for each channel and note off event for each note.

```python


n.panic()


```"""
		pass
	def sendDamperPedal(self, channel,value) -> None: 
		"""Sends a Damper Pedal event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendDamperPedal(1,14)


```"""
		pass
	def sendChannelPressure(self, channel, value) -> None: 
		"""Sends a Channel Pressure event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The channel pressure.  Valid ranges are dependent on the Note Normalize parameter.

```python


n.sendChannelPressure(1, 10)


```"""
		pass
	def sendControl(self, channel, index, value) -> None: 
		"""Sends a Controller event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* index - The MIDI controller index.  Valid ranges are 0 to 127, or 1 to 128, dependent on the One Based Index parameter..

* value - The MIDI control value.  Valid ranges are determined by the CHOP Controller Normalize and Controller Format parameters.

```python


n.sendControl(1, 10, 100)


```"""
		pass
	def sendDataDecrement(self, channel,value) -> None: 
		"""Sends a Data Decrement event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendDataDecrement(1,17)


```"""
		pass
	def sendAllNotesOff(self, channel,value) -> None: 
		"""Sends a All Notes Off event through the CHOP.

* channel - The MIDI event channel. Valid ranges are 1 to 16.

* value - The MIDI value. Valid ranges are 0 to 127.

```python


n.sendAllNotesOff(1,125)


```"""
		pass
	def sendSoundController(self, channel, index,value) -> None: 
		"""Sends a Sound Controller event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* index - Valid index ranges are 1 to 10.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendSoundController(1,5,29)


```"""
		pass
	def sendBankSelect(self, channel,value) -> None: 
		"""Sends a Bank Select event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendBankSelect(1, 65)


```"""
		pass
	def sendMainVolume(self, channel, value) -> None: 
		"""Sends a Main Volume event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendMainVolume(1, 100)


```"""
		pass
	def sendSoftPedal(self, channel,value) -> None: 
		"""Sends a Soft Pedal event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendSoftPedal(1,20)


```"""
		pass
	def sendLocalControl(self, channel,value) -> None: 
		"""Sends a Local Control Controllers event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendLocalControl(1,87)


```"""
		pass
	def sendPolyOn(self, channel,value) -> None: 
		"""Sends a Poly On/Mono Off event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendPolyOn(1,16)


```"""
		pass
	def sendPan(self, channel, value) -> None: 
		"""Sends a Pan event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendPan(1, 45)


```"""
		pass
	def sendResetAllControllers(self, channel,value) -> None: 
		"""Sends a Reset All Controllers event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendResetAllControllers(1,34)


```"""
		pass
	def sendBreathController(self, channel, value) -> None: 
		"""Sends a Breath Controller event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendBreathController(1, 12)


```"""
		pass
	def sendPortamentoTime(self, channel, value) -> None: 
		"""Sends a Portamento Time event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendPortamentoTime(1, 78)


```"""
		pass
	def sendDataIncrement(self, channel,value) -> None: 
		"""Sends a Data Increment event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendDataIncrement(1,17)


```"""
		pass
	def sendFootController(self, channel, value) -> None: 
		"""Sends a Foot Controller event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendFootController(1, 12)


```"""
		pass
	def sendHold2(self, channel,value) -> None: 
		"""Sends a Hold2 event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendHold2(1,55)


```"""
		pass
	def sendSostenuto(self, channel,value) -> None: 
		"""Sends a Sostenuto event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendSostenuto(1,42)


```"""
		pass
	def sendOmniOff(self, channel,value) -> None: 
		"""Sends a Omni Off event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendOmniOff(1,91)


```"""
		pass
	def sendGeneralPurposeController(self, channel, index,value) -> None: 
		"""Sends a General Purpose Controller event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* index - Valid index ranges are 1 to 8.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendGeneralPurposeController(1,3,76)


```"""
		pass
	def sendNoteOff(self, channel, index, value) -> None: 
		"""Sends a Note Off event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* index - The MIDI index/note.  Valid ranges are 0 to 127, or 1 to 128, dependent on the One Based Index parameter.

* value - (Optional) The MIDI note value.  Valid ranges are determined by the CHOP Note Normalize parameter. Minimum when not specified.

```python


n.sendNoteOff(1, 63)


```"""
		pass
	def sendExclusive(self, message1, message2, *args) -> None: 
		"""Send a sytem exclusive message through this CHOP. The System Exclusive start and end character are added to the message.

Messages can any combination of strings, byte arrays, or individual single-byte numeric values.

To serialize non-byte values (example floats or integers) there are several python modules to do this, such as pickle or struct.

```python


n.sendExclusive(0xb0, 'abc' ,0x40)  # Send a system exclusive message consisting of a start byte, 0xb0, 'a', 'b', 'c' (as ascii), 0x40, and an end byte.


```"""
		pass
	def sendPortamento(self, channel,value) -> None: 
		"""Sends a Portamento event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendPortamento(1,34)


```"""
		pass
	def sendEffectControl(self, channel, index,value) -> None: 
		"""Sends a Main Volume event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* index - Valid index ranges are 1 to 2.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendEffectControl(1,1,27)


```"""
		pass
	def sendLegatoFootswitch(self, channel,value) -> None: 
		"""Sends a Legato Footswitch event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendLegatoFootswitch(1,07)


```"""
		pass
	def sendModulationWheel(self, channel,value) -> None: 
		"""Sends a Modulation Wheel event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendModulationWheel(1, 65)


```"""
		pass
	def sendProgram(self, channel, value) -> None: 
		"""Sends a Program Change event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI program change.  Valid ranges are dependent on the Controller Normalize parameter.

```python


n.sendProgram(1, 10)


```"""
		pass
	def sendOmniOn(self, channel,value) -> None: 
		"""Sends a Omni On event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendOmniOn(1,41)


```"""
		pass
	def sendPortamentoControl(self, channel,value) -> None: 
		"""Sends a Portamento Control event through the CHOP.

* channel - The MIDI event channel.  Valid ranges are 1 to 16.

* value - The MIDI value.  Valid ranges are 0 to 127.

```python


n.sendPortamentoControl(1,112)


```"""
		pass
	pass


class midiinmapCHOP(CHOP,OP):
	""""""
	par : parameter.midiinmapCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.midiinmapCHOP & parameter.CHOP & parameter.OP"""
	pass


class midiinCHOP(CHOP,OP):
	""""""
	par : parameter.midiinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.midiinCHOP & parameter.CHOP & parameter.OP"""
	pass


class mergeCHOP(CHOP,OP):
	""""""
	par : parameter.mergeCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.mergeCHOP & parameter.CHOP & parameter.OP"""
	pass


class mathCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.mathCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.mathCHOP & parameter.CHOP & parameter.OP"""
	pass


class ltcoutCHOP(CHOP,OP):
	""""""
	par : parameter.ltcoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.ltcoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class ltcinCHOP(CHOP,OP):
	""""""
	par : parameter.ltcinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.ltcinCHOP & parameter.CHOP & parameter.OP"""
	pass


class lookupCHOP(CHOP,OP):
	""""""
	par : parameter.lookupCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.lookupCHOP & parameter.CHOP & parameter.OP"""
	pass


class logicCHOP(CHOP,OP):
	""""""
	par : parameter.logicCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.logicCHOP & parameter.CHOP & parameter.OP"""
	pass


class limitCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.limitCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.limitCHOP & parameter.CHOP & parameter.OP"""
	pass


class lfoCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.lfoCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.lfoCHOP & parameter.CHOP & parameter.OP"""
	pass


class leuzerod4CHOP(CHOP,OP):
	""""""
	par : parameter.leuzerod4CHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.leuzerod4CHOP & parameter.CHOP & parameter.OP"""
	pass


class leapmotionCHOP(CHOP,OP):
	""""""
	par : parameter.leapmotionCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.leapmotionCHOP & parameter.CHOP & parameter.OP"""
	pass


class lagCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.lagCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.lagCHOP & parameter.CHOP & parameter.OP"""
	pass


class kinectCHOP(CHOP,OP):
	""""""
	par : parameter.kinectCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.kinectCHOP & parameter.CHOP & parameter.OP"""
	pass


class keyframeCHOP(CHOP,OP):
	""""""
	par : parameter.keyframeCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.keyframeCHOP & parameter.CHOP & parameter.OP"""
	pass


class keyboardinCHOP(CHOP,OP):
	""""""
	par : parameter.keyboardinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.keyboardinCHOP & parameter.CHOP & parameter.OP"""
	pass


class joystickCHOP(CHOP,OP):
	""""""
	par : parameter.joystickCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.joystickCHOP & parameter.CHOP & parameter.OP"""
	pass


class joinCHOP(CHOP,OP):
	""""""
	par : parameter.joinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.joinCHOP & parameter.CHOP & parameter.OP"""
	pass


class inversekinCHOP(CHOP,OP):
	""""""
	par : parameter.inversekinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.inversekinCHOP & parameter.CHOP & parameter.OP"""
	pass


class inversecurveCHOP(CHOP,OP):
	""""""
	par : parameter.inversecurveCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.inversecurveCHOP & parameter.CHOP & parameter.OP"""
	pass


class interpolateCHOP(CHOP,OP):
	""""""
	par : parameter.interpolateCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.interpolateCHOP & parameter.CHOP & parameter.OP"""
	pass


class infoCHOP(CHOP,OP):
	""""""
	par : parameter.infoCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.infoCHOP & parameter.CHOP & parameter.OP"""
	pass


class inCHOP(CHOP,OP):
	""""""
	par : parameter.inCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.inCHOP & parameter.CHOP & parameter.OP"""
	pass


class holdCHOP(CHOP,OP):
	""""""
	par : parameter.holdCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.holdCHOP & parameter.CHOP & parameter.OP"""
	pass


class hokuyoCHOP(CHOP,OP):
	""""""
	par : parameter.hokuyoCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.hokuyoCHOP & parameter.CHOP & parameter.OP"""
	pass


class hogCHOP(CHOP,OP):
	""""""
	par : parameter.hogCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.hogCHOP & parameter.CHOP & parameter.OP"""
	pass


class heliosdacCHOP(CHOP,OP):
	""""""
	par : parameter.heliosdacCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.heliosdacCHOP & parameter.CHOP & parameter.OP"""
	pass


class handleCHOP(CHOP,OP):
	""""""
	par : parameter.handleCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.handleCHOP & parameter.CHOP & parameter.OP"""
	pass


class gestureCHOP(CHOP,OP):
	""""""
	par : parameter.gestureCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.gestureCHOP & parameter.CHOP & parameter.OP"""
	pass


class functionCHOP(CHOP,OP):
	""""""
	par : parameter.functionCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.functionCHOP & parameter.CHOP & parameter.OP"""
	pass


class filterCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.filterCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.filterCHOP & parameter.CHOP & parameter.OP"""
	pass


class fileoutCHOP(CHOP,OP):
	""""""
	par : parameter.fileoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.fileoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class fileinCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	curVal : float
	"""The current value of the sample being overridden."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	par : parameter.fileinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.fileinCHOP & parameter.CHOP & parameter.OP"""
	pass


class feedbackCHOP(CHOP,OP):
	""""""
	par : parameter.feedbackCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.feedbackCHOP & parameter.CHOP & parameter.OP"""
	pass


class fanCHOP(CHOP,OP):
	""""""
	par : parameter.fanCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.fanCHOP & parameter.CHOP & parameter.OP"""
	pass


class extendCHOP(CHOP,OP):
	""""""
	par : parameter.extendCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.extendCHOP & parameter.CHOP & parameter.OP"""
	pass


class expressionCHOP(CHOP,OP):
	""""""
	chanIndex : any
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	inputVal : any
	"""The current value of the input sample being evaluated.  To access channels from other inputs use the [[OP_Class#Connection|operator's inputs]]. Example:  me.inputs[1]['chan4'] will access chan4 of the second input."""
	sampleIndex : any
	"""The index of the current sample being evaluated."""
	par : parameter.expressionCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.expressionCHOP & parameter.CHOP & parameter.OP"""
	pass


class eventCHOP(CHOP,OP):
	""""""
	par : parameter.eventCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.eventCHOP & parameter.CHOP & parameter.OP"""
	def releaseEvent(self, id) -> int: 
		"""Manually release an event created with createEvent(hold=True) method above.

Returns the number of events released.

* id - (Optional) Specifies the event to release. If not specified, all events are released."""
		pass
	def createEvent(self, hold=False, samples=[], index=0, attackTime, attackLevel, decayTime, sustainTime, sustainMin, sustainMax, releaseTime, releaseLevel, speed) -> int: 
		"""Manually create an event for this CHOP. You still need an input attached, but it can stay at 0 and you can create events from this method.

Returns the id of the created particle.

*  hold - (Optional) Specifies whether the event will hold the sustain state.  When True, can be released with the releaseEvent method.

*  samples - (Optional) A list of values to override the Samples Input.

*  index - (Optional) Specifies the input trigger index to assign to this event.

*  attackTime - (Optional) If not specified, read from parameter.

*  attackLevel - (Optional) If not specified, read from parameter.

*  decayTime - (Optional) If not specified, read from parameter.

*  sustainTime - (Optional) If not specified, read from parameter.

*  sustainMin - (Optional) If not specified, read from parameter.

*  sustainMax - (Optional) If not specified, read from parameter.

*  releaseTime - (Optional) If not specified, read from parameter.

*  releaseLevel - (Optional) If not specified, read from parameter.

*  speed - (Optional) If not specified, read from parameter."""
		pass
	pass


class etherdreamCHOP(CHOP,OP):
	""""""
	par : parameter.etherdreamCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.etherdreamCHOP & parameter.CHOP & parameter.OP"""
	pass


class envelopeCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.envelopeCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.envelopeCHOP & parameter.CHOP & parameter.OP"""
	pass


class dmxoutCHOP(CHOP,OP):
	""""""
	par : parameter.dmxoutCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.dmxoutCHOP & parameter.CHOP & parameter.OP"""
	pass


class dmxinCHOP(CHOP,OP):
	""""""
	par : parameter.dmxinCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.dmxinCHOP & parameter.CHOP & parameter.OP"""
	pass


class deleteCHOP(CHOP,OP):
	""""""
	par : parameter.deleteCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.deleteCHOP & parameter.CHOP & parameter.OP"""
	pass


class delayCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.delayCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.delayCHOP & parameter.CHOP & parameter.OP"""
	pass


class dattoCHOP(CHOP,OP):
	""""""
	inputCell : td.Cell
	"""The current input [[Cell Class|cell]] being evaluated. From the [[Cell Class|cell]] you can get its row, column and value. e.g. me.inputCell.val or use the specific members listed below."""
	inputCol : td.Col
	"""The current input colunn being evaluated."""
	inputRow : td.Row
	"""The current input row being evaluated."""
	inputTable : OP
	"""The current input [[DAT Class|DAT]] being evaluated."""
	par : parameter.dattoCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.dattoCHOP & parameter.CHOP & parameter.OP"""
	pass


class cycleCHOP(CHOP,OP):
	""""""
	par : parameter.cycleCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.cycleCHOP & parameter.CHOP & parameter.OP"""
	pass


class crossCHOP(CHOP,OP):
	""""""
	par : parameter.crossCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.crossCHOP & parameter.CHOP & parameter.OP"""
	pass


class cplusplusCHOP(CHOP,OP):
	""""""
	par : parameter.cplusplusCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.cplusplusCHOP & parameter.CHOP & parameter.OP"""
	pass


class countCHOP(CHOP,OP):
	""""""
	par : parameter.countCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.countCHOP & parameter.CHOP & parameter.OP"""
	pass


class copyCHOP(CHOP,OP):
	""""""
	chanIndex : int
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	sampleIndex : int
	"""The index of the current sample being evaluated."""
	copyIndex : int
	"""The current copy index, beginning at zero."""
	par : parameter.copyCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.copyCHOP & parameter.CHOP & parameter.OP"""
	pass


class constantCHOP(CHOP,OP):
	""""""
	par : parameter.constantCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.constantCHOP & parameter.CHOP & parameter.OP"""
	pass


class compositeCHOP(CHOP,OP):
	""""""
	chanIndex : any
	"""```me.chanIndex</code> can be used in any parameter to give a different value for each [[Channel Class|channel]] being generated, for example <code>[3, 4, 5][me.chanIndex]```."""
	par : parameter.compositeCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.compositeCHOP & parameter.CHOP & parameter.OP"""
	pass


class clockCHOP(CHOP,OP):
	""""""
	par : parameter.clockCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.clockCHOP & parameter.CHOP & parameter.OP"""
	pass


class clipCHOP(CHOP,OP):
	""""""
	par : parameter.clipCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.clipCHOP & parameter.CHOP & parameter.OP"""
	pass


class clipblenderCHOP(CHOP,OP):
	""""""
	clipA : OP
	"""The clip being executed or blended from."""
	clipB : OP
	"""The clip being blended into."""
	currentClip : OP
	"""Clip A before the start of a transition, clip B otherwise."""
	currentFrame : float
	"""The frame index of the current clip output."""
	currentTime : float
	"""The time value of the current clip output."""
	endBlendTime : float
	"""The time at which the transition is complete."""
	isBlending : bool
	"""True if the output is transitioning between clips."""
	isQueued : bool
	"""True if transitions are delayed until current transition completes."""
	isTriggerWaiting : bool
	"""True if there is a pending triggered transition."""
	lastClipA : float
	"""Last value of clip A."""
	lastClipB : float
	"""Last value of clip B."""
	nextClip : OP
	"""The next clip to be sequenced."""
	startBlendTime : float
	"""The time the transition will start."""
	triggerClip : OP
	"""The clip ."""
	par : parameter.clipblenderCHOP|parameter.CHOP|parameter.OP
	"""Parameters of parameter.clipblenderCHOP & parameter.CHOP & parameter.OP"""
	def trigger(self, clipCHOP, waitEnd=False) -> None: 
		"""Trigger the next clip in sequence.

* clipCHOP - (Optional) If specified, the Clip CHOP it is inserted into the queue.

* waitEnd - When True, wait until the end of the current clip before triggering."""
		pass
	pass


class chopexecuteDAT(DAT,OP):
	""""""
	par : parameter.chopexecuteDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.chopexecuteDAT & parameter.DAT & parameter.OP"""
	pass


class choptoDAT(DAT,OP):
	""""""
	par : parameter.choptoDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.choptoDAT & parameter.DAT & parameter.OP"""
	pass


class choptoSOP(SOP,OP):
	""""""
	par : parameter.choptoSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.choptoSOP & parameter.SOP & parameter.OP"""
	pass


class choptoTOP(TOP,OP):
	""""""
	par : parameter.choptoTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.choptoTOP & parameter.TOP & parameter.OP"""
	pass


class chromakeyTOP(TOP,OP):
	""""""
	par : parameter.chromakeyTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.chromakeyTOP & parameter.TOP & parameter.OP"""
	pass


class circleSOP(SOP,OP):
	""""""
	par : parameter.circleSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.circleSOP & parameter.SOP & parameter.OP"""
	pass


class circleTOP(TOP,OP):
	""""""
	par : parameter.circleTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.circleTOP & parameter.TOP & parameter.OP"""
	pass


class claySOP(SOP,OP):
	""""""
	par : parameter.claySOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.claySOP & parameter.SOP & parameter.OP"""
	pass


class clipDAT(DAT,OP):
	""""""
	par : parameter.clipDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.clipDAT & parameter.DAT & parameter.OP"""
	pass


class clipSOP(SOP,OP):
	""""""
	par : parameter.clipSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.clipSOP & parameter.SOP & parameter.OP"""
	pass


class COMP(OP):
	"""A COMP describes a reference to a [[Component]] operator."""
	extensions : List
	"""A list of [[Extensions|extensions]] attached to this component."""
	extensionsReady : Bool
	"""True unless the extensions are currently compiling. Can be used to avoid accessing promoted members prematurely during an extension initialization function."""
	internalOPs : Dict
	"""A dictionary of [[Internal_Operators|internal operator shortcuts]] found in this component. See also [[OP_Class#General|OP.iop]]"""
	internalPars : Dict
	"""A dictionary of [[Internal_Parameters|internal parameters shortcuts]] found in this component. See also [[OP_Class#General|OP.ipar]]"""
	clones : List
	"""A list of all [[COMP Class|components]] cloned to this component."""
	componentCloneImmune : Bool
	"""Get or set [[Immune Flag|component clone Immune flag]]. This works together with the cloneImmune member of the [[OP_Class]]. When componentCloneImmune is True, everything inside the clone is [[immune]]. When componentCloneImmune is False, it uses the [[OP_Class]] cloneImmune member to determine if just the component is immune (its parameters etc, but not the component's network inside)."""
	vfs : vfs
	"""An intermediate [[VFS Class|VFS object]] from which embedded [[VFSFile Class|VFSFile objects]] can be accessed. For more information see [[Virtual File System]]."""
	dirty : Bool
	"""True if the contents of the component need to be saved."""
	externalTimeStamp : Time
	"""Time stamp of the external tox file when it was last saved or loaded."""
	currentChild : OP
	"""The child [[OP Class|operator]] that is currently selected. To make an operator current, use its own [[OP Class#Common Flags|OP.current]] method."""
	selectedChildren : List
	"""The list of currently selected [[OP Class|children]]. To change an individual operator's selection state, use its own [[OP Class#Common Flags|OP.selected]] method."""
	cpuCookTime : float
	"""Duration of the last measured cook in CPU time (in milliseconds)."""
	childrenCPUCookTime : float
	"""The total accumulated cook time of all children of this operator during the last frame. Zero if the operator is not a COMP and/or has no children."""
	childrenCPUCookAbsFrame : int
	"""The absolute frame on which childrenCookTime is based."""
	gpuMemory : int
	"""The amount of GPU memory this OP is using, in bytes."""
	pickable : Bool
	"""Get or set [[Pickable Flag|pickable flag]]."""
	utility : Bool
	"""Get or set utility flag."""
	isCOMP : Bool
	"""True if the operator is a component."""
	isPrivate : Bool
	"""True if the the component contents cannot be directly viewed."""
	isPrivacyActive : Bool
	"""True if the component is private, and privacy is active. When inactive the contents can be temporarily viewed."""
	isPrivacyLicensed : Bool
	"""True if the component is private and if the required CodeMeter license is present to run it."""
	privacyFirmCode : int
	"""The CodeMeter firm code needed to use this private component. 0 if this component is not private using a CodeMeter dongle."""
	privacyProductCode : int
	"""The CodeMeter product code needed to use this private component. 0 if this component is not private using a CodeMeter dongle."""
	privacyDeveloperName : string
	"""The name of the developer of this private component."""
	privacyDeveloperEmail : string
	"""The email of the developer of this private component."""
	inputCOMPs : List
	"""List of input [[COMP Class|components]] to this component through its top connector."""
	inputCOMPConnectors : List
	"""List of input [[Connector Class|connectors]] (on the top) associated with this component."""
	outputCOMPs : List
	"""List of output [[COMP Class|components]] from this component through its bottom connector."""
	outputCOMPConnectors : List
	"""List of output [[Connector Class|connectors]] (on the bottom) associated with this component."""
	par : parameter.COMP|parameter.OP
	"""Parameters of parameter.COMP & parameter.OP"""
	def create(self, opType, name, initialize=True) -> OP: 
		"""Create a new node of the given type, inside this component. If ```name</code> is supplied the new node will use that name, or the next numbered name if its already in use.  opType can be a specific type object, example <code>waveCHOP</code>, or it can be a string <code>'waveCHOP'</code>.  If given an actual instance of a node <code>n</code>, these can be accessed via <code>type(n)</code> and <code>n.OPType``` respectively.

An initialization script associated with the operator is run, unless initialize=False.

The new node is returned.

* opType - The python OP type for the type of operator you want to create.

* name - (Optional) The name for the new operator. If there already is an operator with that name, the next numbered name will be used.

* initialize - (Keyword, Optional) If set to false, then the initialization script for that node won't be run. Most nodes don't do anything to initialize, but some do. For example the Light COMP initializes a network inside itself of SOPs.

```python


n.create(waveCHOP)

w = n.create(boxSOP, 'box12')


```"""
		pass
	def collapseSelected(self, ) -> None: 
		"""Move all selected operators into a new [[Base COMP]]. Equivalent to right-click on the network background and choosing Collapse Selected."""
		pass
	def copy(self, OP, name=None, includeDocked=True) -> OP: 
		"""Copy the operator into this component. If name is supplied, the new node will use that name. The new node is returned.

* OP - The operator to copy. This is not a string, it must be an OP.

* name - (Keyword, Optional) If provided, the new node will have this name. If there already is an operator with that name, the next numbered name will be used.

* includeDocked - (Keyword, Optional) When true a copy will include any externally docked operators to the source component.

```python


w = n.copy( op('wave1') )


```"""
		pass
	def copyOPs(self, listOfOPs) -> any: 
		"""Copy a list of operators into this component.

This is preferred over multiple single copies, as connections between the operators are preserved.

A new list with the created operators is returned.

* listOfOPs - A list containing one or more OPs to be copied.

```python


alist = [op('wave1'), op('wave2')]

n.copyOPs(alist)


```"""
		pass
	def findChildren(self, type=None, name=None, path=None, depth=None, maxDepth=None, text=None, comment=None, tags=[], allTags=False, parValue=None, parExpr=None, parName=None, onlyNonDefaults=False, includeUtility=False, key=None) -> any: 
		"""Return a list of [[OP Class|operators]] matching the specified criteria.

* type - (Keyword, Optional) Specify the type of OP.  Example type=boxSOP

* name - (Keyword, Optional) Specify the name of the OP. [[Pattern Matching]] supported. Example: name='project* '

* path - (Keyword, Optional) Specify the path of the OP. [[Pattern Matching]] supported. Example: path='* /pics/* '

* depth - (Keyword, Optional) Specify the relative depth of the OP to the calling OP.  Children have depth 1, their children have depth 2, etc.

* maxDepth - (Keyword, Optional) Specify the maximum relative depth of the OP from the calling OP.

* text - (Keyword, Optional) Specify the DAT contents of the OP.  [[Pattern Matching]] supported.  Example: text='* import* '

* comment - (Keyword, Optional) Specify the OP comment.  [[Pattern Matching]] supported.  Example: comment='* todo* '

* tags - (Keyword, Optional) Specify a list of tags to search. [[Pattern Matching]] supported.  Example: tags=['* sequencer* ', '* interface* ']

* allTags - (Keyword, Optional) When True, only include OPs where all specified tags are matched.

* parValue - (Keyword, Optional) Specify the value of any parameters in the OP.  [[Pattern Matching]] supported.  Example: parValue='500'

* parExpr - (Keyword, Optional) Specify the expression of any parameters in the OP.  [[Pattern Matching]] supported.  Example: parExpr='* sin* '

* parName - (Keyword, Optional) Specify the name of any parameters in the OP.  [[Pattern Matching]] supported.  Example: parName='clone'

* onlyNonDefaults - (Keyword, Optional) When True, only non default parameters are included.

* includeUtility - (Keyword, Optional) If specified, controls whether or not [[Network Utilities: Comments, Network Boxes, Annotates|Utility nodes]] (e.g. Comments) are included in the results.

* key - (Keyword, Optional) Specify a custom search function.

```python


#find all OPs whose name begins with circle

n.findChildren(name='circle* ')



#find all wide CHOPs

n.findChildren(type=CHOP, key = lambda x: x.nodeWidth > 200)



#find all COMPs specifying clones

n.findChildren(type=COMP, parName='clone', onlyNonDefaults=True)


```"""
		pass
	def initializeExtensions(self, index=None) -> any: 
		"""Initialize the components [[Extensions|extensions]]. To initialize an individual extension, specify its index.

Returns the compiled extension.

* index - (Optional) Index to initialize. 0 = first extension, etc.

```python


n.initializeExtensions(0) # initialize first extension.


```"""
		pass
	def loadTox(self, filepath, unwired=False, pattern=None, password=None) -> OP: 
		"""Load the component from the given file path into this component.

* filepath - The path and filename of the ```.tox``` to load.

* unwired - (Keyword, Optional) If True, the component inputs will remain unwired.

* pattern - (Keyword, Optional) Can be specified to only load operators within the component that match the pattern. Wildcards are not supported.

* password - (Keyword, Optional) If specified, decrypts the tox with the password."""
		pass
	def loadByteArray(self, byteArray, unwired=False, pattern=None, password=None) -> OP: 
		"""Load the component from the given bytearray into this COMP. See .saveByteArray() as a way to generate this byteArray.

* bytearray - A bytearray containing the component, from a call to saveByteArray().

* unwired - (Keyword, Optional) If True, the component inputs will remain unwired.

* pattern - (Keyword, Optional) Can be specified to only load operators within the component that match the pattern. Wildcards are not supported.

* password - (Keyword, Optional) If specified, decrypts the component with the password.'"""
		pass
	def reload(self, filepath, password=None) -> None: 
		"""Reloads the component from the given file path. This will replace its children as well as top level parameters and update flags, node width/height, storage, comments and inputs (but keep original node x,y).

* filepath - The path and filename of the .tox to load.

* password - (Keyword, Optional) If specified, decrypts the component with the password.'"""
		pass
	def resetNetworkView(self, recurse) -> None: 
		"""Reset the network view such that the network editor will be re-homed upon entering this component.

* recurse - (Optional) When True, resets network view of all children components as well. Default False.

```python


n.resetNetworkView(True) # reset network view of n and all its children.


```"""
		pass
	def save(self, filepath, createFolders=False, password=None) -> Path: 
		"""Saves the component to disk. If no path is provided, a default filename is used and the ```.tox</code> is saved to <code>project.folder```.

Returns the filename used.

* filepath - (Optional) The path and filename to save the ```.tox``` to.

* createFolders - (Keyword, Optional) If True, it creates the not existent directories provided by the filepath.

* password - (Keyword, Optional) If specified, encrypts the tox with the password.

```python


name = n.save() # save in native tox format with default name

n.save('output.tox')  # supply name

n.save('C:/Desktop/myFolder/output.tox', createFolders=True)  # supply name and createFolder flag


```"""
		pass
	def saveByteArray(self, password=None) -> bytearray: 
		"""Save the component into a bytearray. The bytearray is the same data that is held in a .tox file. ```loadByteArray()``` can be used to load the component.

* password - (Keyword, Optional) If specified, encrypts the tox with the password."""
		pass
	def saveExternalTox(self, recurse=False, password=None) -> int: 
		"""Save out the contents of any COMP referencing an external .tox

Returns the number of components saved.

* recurse - (Keyword, Optional) If set to True, child components are included in the operation.

* password - (Keyword, Optional) If specified, encrypts the tox with the password.

```python


root.saveExternalTox(recurse=True)

op('geo1').saveExternalTox(recurse=False)


```"""
		pass
	def appendCustomPage(self, name) -> Page: 
		"""Add a new [[Page Class|page]] of custom parameters. See [[Page Class]] for more details. See [[Custom Parameters]] for the procedure.

```python


n = op('base1')

page = n.appendCustomPage('Custom1')

page.appendFloat('X1')


```"""
		pass
	def destroyCustomPars(self, ) -> any: 
		"""Remove all custom parameters from COMP."""
		pass
	def sortCustomPages(self, page1, page2, page3, *args) -> None: 
		"""Reorder custom parameter pages by listing their page names.

```python


n = op('base1')

n.sortCustomPages('Definition','Controls')


```"""
		pass
	def accessPrivateContents(self, key) -> any: 
		"""Gain access to a private component.  The component will still be private the next time it is saved or re-opened.

Returns true when the key is correct, and access is granted. If dongle privacy is being used, no arguments are required.

* key - (Optional) The existing key phrase. This should resolve to a non-blank string. Not required for dongle privacy.

```python


n.accessPrivateContents('secret')


```"""
		pass
	def addPrivacy(self, key, developerName=None) -> None: 
		"""Add privacy to a component with the given key.

Privacy can only be added to components that currently have no privacy. Adding Privacy requires a Pro license.

* key - The new key phrase. This should resolve to a non-blank string.

```python


n.addPrivacy('secret')


```"""
		pass
	def addPrivacy(self, firmCode, productCode, developerName=None, developerEmail=None) -> None: 
		"""Add privacy to a component with the given CodeMeter firm code and product code.

Privacy can only be added to components that currently have no privacy. Adding Privacy requires a Pro license.



The first bit of the CodeMeter Dongle's Feature Map must be set to enable privacy and add prodcut code as well as to access the private component in edit mode later.



The private component can be used with any Dongle matching the firm code and product code without the first Feature Map bit set. In this case the component will run in private mode keeping the contents of the component hidden.

* firmCode - The CodeMeter firm code to use.

* productCode - The CodeMeter product code to use.

```python


n.addPrivacy(10, 4)


```"""
		pass
	def blockPrivateContents(self, key) -> None: 
		"""Block access to a private component that was temporarily accessible.

```python


n.blockPrivateContents()


```"""
		pass
	def removePrivacy(self, key) -> any: 
		"""Completely remove privacy from a component.

Returns true when the key is correct.

* key - The existing key phrase. This should resolve to a non-blank string.

```python


n.removePrivacy('secret')


```"""
		pass
	def setVar(self, name, value) -> None: 
		"""Set a component variable to the specified value.

* name - The variable name to use.

* value - The value for this variable."""
		pass
	def unsetVar(self, name) -> None: 
		"""Unset the specified component variable. This removes the entry from the '```local/set_variables```' table, if found.

* name - The name of the variable to unset."""
		pass
	def vars(self, pattern1, pattern2, *args) -> any: 
		"""Return a list of all component variables in this COMP. Optional name patterns may be specified.

* pattern -  (Optional) The name(s) of variables whose values should be returned. [[Pattern Matching]] can be used.

```python


a = n.vars()

a = n.vars('A* ', 'B* ')


```"""
		pass
	pass


class windowCOMP(COMP,OP):
	""""""
	scalingMonitorIndex : int
	"""The index of the monitor whose DPI scale is being used to for the Window. This is the usually the monitor the window is covering the most."""
	isBorders : bool
	"""True if the window is bordered."""
	isFill : bool
	"""True if the window will stretch its contents to fill its specified area."""
	isOpen : bool
	"""True when window is open."""
	width : int
	"""Window width. Expressed in points or pixels, depending on the DPI Scaling parameter of the Window COMP."""
	height : int
	"""Window height. Expressed in points or pixels, depending on the DPI Scaling parameter of the Window COMP."""
	x : int
	"""Window X coordinate relative to the bottom left of the main monitor. Expressed in points or pixels, depending on the DPI Scaling parameter of the Window COMP."""
	y : int
	"""Window Y coordinate relative to the bottom left of the main monitor. Expressed in points or pixels, depending on the DPI Scaling parameter of the Window COMP."""
	contentX : int
	"""X position of left edge of the windows contents. Ignores borders if they are present. Expressed in points or pixels, depending on the 'DPI Scaling' parameter setting."""
	contentY : int
	"""Y position of bottom edge of the windows contents. Ignores borders if they are present. Expressed in points or pixels, depending on the 'DPI Scaling' parameter setting."""
	contentWidth : int
	"""Width of windows contents. Ignores borders if they are present. Expressed in points or pixels, depending on the 'DPI Scaling' parameter setting."""
	contentHeight : int
	"""Height of windows contents. Ignores borders if they are present. Expressed in points or pixels, depending on the 'DPI Scaling' parameter setting."""
	par : parameter.windowCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.windowCOMP & parameter.COMP & parameter.OP"""
	def setForeground(self, ) -> bool: 
		"""Activates the window, sets it to the foregound and other visual cues. Sets focus and increases process priority.

Can only be called by a foreground process, or a child of a foreground process.

Returns true if successful."""
		pass
	pass


class timeCOMP(COMP,OP):
	""""""
	frame : float
	"""Get or set the current frame output by this component."""
	seconds : float
	"""Get or set the current time output by this component (expressed in seconds)."""
	rate : float
	"""Get or set the frames per second, (or rate)."""
	play : bool
	"""Get or set whether the component is playing."""
	timecode : str
	"""Get or set the current timecode generated by this component."""
	start : float
	"""Get or set start of main frame range."""
	end : float
	"""Get or set end of main frame range."""
	rangeStart : float
	"""Get or set start of sub frame range. Must be within main start, end range"""
	rangeEnd : float
	"""Get or set end of sub frame range. Must be within main start, end range."""
	loop : bool
	"""Get or set whether the timeline loops."""
	independent : float
	"""Get or set whether the timeline runs independently of other timelines."""
	tempo : float
	"""Get or set beats per minute."""
	signature1 : int
	"""Get or set time signature, first value."""
	signature2 : int
	"""Get or set time signature, second value."""
	par : parameter.timeCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.timeCOMP & parameter.COMP & parameter.OP"""
	pass


class replicatorCOMP(COMP,OP):
	""""""
	curItem : OP
	"""Reference to the current [[operator]] replicant."""
	par : parameter.replicatorCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.replicatorCOMP & parameter.COMP & parameter.OP"""
	pass


class PanelCOMP(COMP,OP):
	"""The PanelCOMP describes an instance of a [[Panel Component]]. The state is represented by [[Panel Value|Panel Values]].

This class inherits from the COMP Class."""
	panel : td.Panel
	"""The [[Panel Class|Panel]] from which [[Panel Value|Panel Values]] and the [[PanelValue Class]] may be accessed. (The second form is usually sufficient.)

```python


v = op('button1').panel.u.val

v = op('button1').panel.u


```
"""
	panelRoot : OP
	"""The panelCOMP at the top of the panel hierarchy."""
	panelChildren : list
	"""The children panelCOMPs of this operator."""
	x : int
	"""The panel's x coordinate, as measured in pixels."""
	y : int
	"""The panel's y coordinate, as measured in pixels."""
	width : int
	"""The panel's width, as measured in pixels."""
	height : int
	"""The panel's height, as measured in pixels."""
	marginX : int
	"""The panel's x coordinate adjusted by margins as measured in pixels."""
	marginY : int
	"""The panel's y coordinate adjusted by margins, as measured in pixels."""
	marginWidth : int
	"""The panel's width adjusted by margins, as measured in pixels."""
	marginHeight : int
	"""The panel's height adjusted by margins, as measured in pixels."""
	par : parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	def panelParent(self, n) -> any: 
		"""The nth panel parent of this operator.  If n not specified, returns the panel parent. If n = 2, returns the parent of the parent, etc. If no panel parent exists at that level, None is returned.  A panel parent is the panel wired to the input of this operator, or if that does not exist, the panel containing this operator.

* n - (Optional) n is the number of levels up to climb. When n = 1 it will return the operator's panel parent.

```python


p = me.panelParent(2) #grandfather


```"""
		pass
	def interactMouse(self, u, v, leftClick=0, middleClick=0, rightClick=0, left=False, middle=False, right=False, wheel=0, pixels=False, Screen=False, quiet=True) -> PanelCOMP: 
		"""Simulates virtual mouse clicks, rollovers, moves and drags on a panel. It will also update the panel values: inside, insideu, insidev, state, u and v, in panels all the way up to the parent panel. The first (primary) mouse down/touch on a panel takes precedence over subsequent mouse downs and touches, and overrides any hovers. The primary state on a panel is global as each panel can only have one interaction updating its state.

* u - The first coordinate for the click to occur at.

* v - The second coordinate for the click to occur at.

* leftClick, middleClick, rightClick -  (Keyword, Optional) Use to specify the number of times a button is clicked on

* left, middle, right -  (Keyword, Optional) Use to specify if the button is being pressed.  When set to False it simulates a mouse move with the button up.  The first time the button is set to True will initiate a virtual mouse down on the child panel at the coordinates u,v.  Subsequent True states will simulate a drag (mouse button down and moving).  Simulate a mouse-up by calling the button set to False, e.g. left=False.

* wheel -  (Keyword, Optional) Roll the mouse wheel

* pixels - (Keyword, Optional) When True, the coordinates are treated as pixel offsets.  When False, they are treated as normalized values.

* screen - (Keyword, Optional) When True, the coordinates are relative to the screen. When False, they are relative to the calling container.

* quiet - (Keyword, Optional) When False, print warning messages, such as starting a mouse-down-move on a panel that is already being moved (dragged).

* aux - (Keyword, Optional) Auxiliary data.

```python


op('container1').interactMouse(0.5, 0.5) # roll over the middle of container1

op('container1').interactMouse(0.5, 0.5, leftClick=2) # double click the middle of container1

op('container1').interactMouse(0.5, 0.5, left=True) # left mouse down on the middle of container1

op('container1').interactMouse(0.6, 0.6, left=True) # move with left mouse down in container1

op('container1').interactMouse(0.6, 0.6) # mouse up

op('container1').interactMouse(0.5, 0.5, wheel=0.3) # roll the mouse wheel in the middle of container1

op('container1').interactMouse(10, 20, pixels=True) # send a mouse event 10 pixels to the right, and 20 pixels above the lower left corner of container1


```"""
		pass
	def interactTouch(self, u, v, hover='id', start='id', move='id', end='id', pixels=False, screen=False, quiet=True, aux='data') -> PanelCOMP: 
		"""Simulates virtual multiple touches and hovers on a panel via user assigned id. It will also update the panel values: inside, insideu, insidev, state, u and v, in panels all the way up to the parent panel. The first (primary) mouse down/touch on a panel takes precedence over subsequent mouse downs and touches, and overrides any hovers. The primary state on a panel is global.

* u - The first coordinate for the click to occur at.

* v - The second coordinate for the click to occur at.

* hover - (Keyword, Optional) Indicates a hover performed by the touch identifiable by 'id'.  If 'id' is used by a touch, the touch is ended.  If the <u,v> is out of bounds, the hover will end.

* start - (Keyword, Optional) Start a touch identifiable by 'id'.  If 'id' is already touching or hovering, the action is ended and a new touch is started.

* move - (Keyword, Optional) Move a touch identifiable by 'id'.  Nothing happens if 'id' is not found.

* end - (Keyword, Optional) End a touch identifiable by 'id'.  Nothing happens if 'id' is not found.

* pixels - (Keyword, Optional) When True, the coordinates are treated as pixel offsets.  When False, they are treated as normalized values.

* screen - (Keyword, Optional) When True, the coordinates are relative to the screen. When False, they are relative to the calling container.

* quiet - (Keyword, Optional) Print warning messages, such as starting a touch down on a panel that already has a touch.

```python


op('container1').interactTouch(0.5, 0.5, hover='finger') # roll over the middle of container1

op('container1').interactTouch(0.5, 0.5, start='finger') # ends the hover and start a touch

op('container1').interactTouch(0.7, 0.5, move='finger') # move the touch

op('container1').interactTouch(0.3, 0.4, start='finger') # ends the previous touch and start a new touch

op('container1').interactTouch(-1, -1, hover='finger') # ends the previous touch, and end any rollover state


```"""
		pass
	def interactClear(self, ) -> None: 
		"""Terminates any existing interactions. Touch or mouse interactions will end. Panels that are hovered over will end their rollover state."""
		pass
	def interactStatus(self, ) -> list: 
		"""Returns a list of panel interactions.  Each interaction is encapsulated in a list as follows: [id, panel, state, primary].

* id - The unique string identifying the interaction.  '__MOUSE__' is used if the interaction was established via interactMouse.

* panel - The child panel being interacted with .

* state - Interaction types 'hover' or 'touch'.

* primary - True if the interaction is the first to act on the panel.

```python


op('container1').interactStatus  # list the current hover over a slider and 2 touches over a button in container1

[['touch1', type:sliderCOMP path:/project1/container1/slider1, 'hover', False],

['__MOUSE__', type:buttonCOMP path:/project1/container1/button1, 'touch', True],

['touch2', type:buttonCOMP path:/project1/container1/button1, 'touch', False]]


```"""
		pass
	def locateMouse(self, ) -> any: 
		"""Returns a tuplet containing the mouse coordinates relative to the [[Panel Component]]. If the mouse is not over a window containing the panel, None is returned instead."""
		pass
	def locateMouseUV(self, ) -> any: 
		"""Returns a tuplet containing the normalized mouse coordinates relative to the [[Panel Component]]. If the mouse is not over a window containing the panel, None is returned instead."""
		pass
	def setFocus(self, moveMouse=False) -> None: 
		"""Set the hierarchical focus to this component, which sets the Panel value focusselect to 1. Focus will only be set successfully if the panel is open.

* moveMouse - (Keyword, Optional) If set to True, the mouse will be moved to the component as well."""
		pass
	pass


class tableCOMP(PanelCOMP,COMP,OP):
	""""""
	par : parameter.tableCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.tableCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	def getRowFromID(self, id) -> int: 
		"""Return the table row value, given a cell ID.

* id - The cell id.  Usually taken from [[PanelValue Class|panel values]]: celloverid, cellfocusid, etc."""
		pass
	def click(self, row, col, clickCount=1, force=False, left=False, middle=False, right=False) -> None: 
		"""Simulate a mouse click on a cell of the table. (0,0) is the top-left cell.

* row, col - The row and column of the cell to click.

* clickCount - (Keyword, Optional), Sets the number of clicks, for double clicking etc.

* force - (Keyword, Optional) Forces the panel click, even if it's disabled.

* left,middle,right - (Keyword, Optional) Override the default mouse button used.  When none are set to true, the left mouse button is pressed, and the other buttons released.

```python


op('table1').click(2,3) #row 2, column 3


```"""
		pass
	def getColFromID(self, id) -> int: 
		"""Return the table column value, given a cell ID.

* id - The cell id.  Usually taken from [[PanelValue Class|panel values]]: celloverid, cellfocusid, etc."""
		pass
	def clickID(self, id, clickCount=1, force=False, left=False, middle=False, right=False) -> None: 
		"""The same as the click method, except it uses a cell ID instead of the row/col to specify the cell to click.

```python


op('table1').clickID(5) # cell id 5


```"""
		pass
	def getCellID(self, row, col) -> int: 
		"""Return the cell ID value, given a row and column.

* row, col - The table component row and column of interest."""
		pass
	def setKeyboardFocus(self, row, col, selectAll=False) -> None: 
		"""Selects and sets the keyboard focus in a cell of the table if the cell is a field.

* row, col -  The row and column of the cell to set the keyboard focus.

* selectAll - (Keyword, Optional) If True, then all text will be selected.

```python


op('table1').select(0, 5) # row 0, column 5, do not select all text


```"""
		pass
	pass


class sliderCOMP(PanelCOMP,COMP,OP):
	""""""
	par : parameter.sliderCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.sliderCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	def click(self, uOrV, v, clickCount=1, force=False, left=False, middle=False, right=False, vOnly=False) -> None: 
		"""Simulate a mouse click of the slider.

If only 1 value is given, it specifies the primary coordinate of the slider. (Either U or V, depending on its type). uOrV and v should be given in normalized coordinates. If two values are given, they specifies both the U and V coordinates.

* uOrV - The first coordinate for the click to occur at. For V slider, this value will be treated as the V coordinate, and nothing needs to be passed into the v argument.

* v - (Optional) The V coordinate to click at. This only needs to be passed if U is being specified in the first argument.

* clickCount - (Keyword, Optional) Sets the number of clicks, for double clicking etc.

* force - (Keyword, Optional) Forces the click to occur, even if the slider is disabled.

* left,middle,right - (Keyword, Optional) Override the default mouse button used.  When none are set, the left mouse button is pressed, and the other buttons released.

* vOnly - (Keyword, Optional) If True and only one coordinate is given on a UV slider, then update the V coordinate only.

```python


op('slider1').click(0.2) #Update U or V on a 1D slider.

op('slider2').click(0.4, 0.5) #Update both U and V on a 2D slider.

op('slider3').click(0.4, vOnly=True) #Update just V on a 2D slider.


```"""
		pass
	pass


class selectCOMP(PanelCOMP,COMP,OP):
	""""""
	par : parameter.selectCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.selectCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	pass


class parameterCOMP(PanelCOMP,COMP,OP):
	""""""
	minWidth : int
	"""The minimum width the parameter dialog can be drawn at before scaling is required."""
	par : parameter.parameterCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.parameterCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	pass


class Pane():
	"""The Pane class describes an instance of a [[Pane|pane]] interface.  It can be accessed through the [[Panes Class|ui.panes]] object. It is the parent class of the [[NetworkEditor Class]]."""
	owner : COMP
	"""Get or set the [[COMP Class|component]] this pane points to."""
	id : int
	"""A unique numeric identifier."""
	link : int
	"""Get or set the numeric link index."""
	enable : bool
	"""Get or set mouse and keyboard interactivity on the pane."""
	maximize : bool
	"""Enable or disable the pane maximize state."""
	name : str
	"""Get or set the pane name."""
	ratio : float
	"""Get or set the split proportion of the pane, if the pane was previously split."""
	bottomLeft : tuple(x,y,u,v)
	"""The coordinates of the bottom left corner, expressed in both pixels and uv offsets, in a named tuple."""
	topRight : tuple(x,y,u,v)
	"""The coordinates of the top right corner, expressed in both pixels and uv offsets, in a named tuple."""
	type : PaneType
	"""The enumerated type of the pane. Example: NetworkEditor.

The enumeration is called PaneType and consists of:

* PaneType.NETWORKEDITOR

* PaneType.PANEL

* PaneType.GEOMETRYVIEWER

* PaneType.TOPVIEWER

* PaneType.CHOPVIEWER

* PaneType.ANIMATIONEDITOR

* PaneType.PARAMETERS

* PaneType.TEXTPORT"""
	par : parameter.Pane
	"""Parameters of parameter.Pane"""
	def changeType(self, paneType) -> any: 
		"""Change the pane to the specified type.  Will return a new Pane object that represents the Pane. After being called, the current Pane instance will no longer be valid.

* paneType - The type of pane to change this pane to.

```python


p = ui.panes[0]

p = p.changeType(PaneType.TOPVIEWER)  # note: must re-assign p to new object.


```"""
		pass
	def close(self, ) -> None: 
		"""Close the pane."""
		pass
	def floatingCopy(self, ) -> any: 
		"""Return a floating copy of the pane."""
		pass
	def splitBottom(self, ) -> any: 
		"""Split the bottom portion of the pane into a new pane."""
		pass
	def splitLeft(self, ) -> any: 
		"""Split the left portion of the pane into a new pane."""
		pass
	def splitRight(self, ) -> any: 
		"""Split the right portion of the pane into a new pane."""
		pass
	def splitTop(self, ) -> any: 
		"""Split the top portion of the pane into a new pane."""
		pass
	def tearAway(self, ) -> bool: 
		"""Detach the pane into a floating window. Returns True if successful."""
		pass
	pass


class opviewerCOMP(PanelCOMP,COMP,OP):
	""""""
	par : parameter.opviewerCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.opviewerCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	def isViewable(self, path) -> bool: 
		"""Returns true if this operator can view the specified operator without recursion issues.'

* path - Path to the specfied operator. An operator can be supplied as well."""
		pass
	pass


class ObjectCOMP(COMP,OP):
	"""This class inherits from the COMP class.

It is the parent class of these subclasses."""
	localTransform : tdu.Matrix
	"""The current local transform of the Object. This is the combination of both the parameters from the Xform and Pre-Xform page, without taking into account any parent or constraint transforms. See also [[Matrix Class]], [[Position Class]] and [[Vector Class]]."""
	worldTransform : tdu.Matrix
	"""The current world transform of the Object."""
	par : parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	def transform(self, ) -> any: 
		"""Gets the current transform of the Object as defined by the Translate, Rotate, Scale and Pivot parameters on the Xform page."""
		pass
	def setTransform(self, matrix) -> None: 
		"""Sets the Translate, Rotate, Scale and Pivot parameters on the Xform page from the given [[Matrix Class|matrix]].

* matrix - A matrix of values."""
		pass
	def preTransform(self, ) -> any: 
		"""Gets the current transform of the Object as defined by the Translate, Rotate, Scale and Pivot parameters on the Pre-Xform page."""
		pass
	def setPreTransform(self, matrix) -> None: 
		"""Sets the Translate, Rotate, Scale and Pivot parameters on the Pre-Xform page from the given [[Matrix Class|matrix]].

* matrix - A matrix of values."""
		pass
	def relativeTransform(self, target) -> any: 
		"""Returns a matrix that is the transform from the called object to the target object. This is, if you transform the called objects current transformation by the returned matrix, it will now be positioned at the target objects positions.

* target - The target [[ObjectCOMP Class|ObjectCOMP]]. See also [[Matrix Class]], [[Position Class]] and [[Vector Class]]."""
		pass
	def importABC(self, filepath, lights=True, cameras=True, mergeGeometry=True, gpuDeform=True, rate=None, textureFolder=None, geometryFolder=None, animationFolder=None) -> None: 
		"""Load ABC files from the given file path.

* filepath - The path and filename of the ABC file to import.

* lights - (Keyword, Optional) If True, lights will be imported.

* cameras - (Keyword, Optional) If True, cameras will be imported.

* mergeGeometry - (Keyword, Optional) If True, geometry will be merged when it is static, and will share materials with other geometry. Less SOPs results in faster rendering, so merge geometry whenever possible.

* gpuDeform - (Keyword, Optional) If True, geometry will be deformed with MATs using the gpu. If False, geometry will be deformed with SOPs using the CPU.

* rate - (Keyword, Optional) If specified, animation channels will sampled at this rate.

* textureFolder - (Keyword, Optional) Texture files (.jpeg, .tiff etc.) will be created in this folder. If the texture files aren't embeded in the .fbx file, you should place the textures in this folder.

* geometryFolder - (Keyword, Optional) Geometry (.tog) files will be created in this folder. If this option is missing, geometry won't be imported.

* animationFolder - (Keyword, Optional) Animation (.bchan) files will be created in this folder. If this option is missing, animation won't be imported."""
		pass
	def importFBX(self, filepath, lights=True, cameras=True, mergeGeometry=True, gpuDeform=True, rate=None, textureFolder=None, geometryFolder=None, animationFolder=None) -> None: 
		"""Load FBX files from the given file path.

* filepath - The path and filename of the FBX file to import.

* lights - (Keyword, Optional) If True, lights will be imported.

* cameras - (Keyword, Optional) If True, cameras will be imported.

* mergeGeometry - (Keyword, Optional) If True, geometry will be merged when it is static, and will share materials with other geometry. Less SOPs results in faster rendering, so merge geometry whenever possible.

* gpuDeform - (Keyword, Optional) If True, geometry will be deformed with MATs using the gpu. If False, geometry will be deformed with SOPs using the CPU.

* rate - (Keyword, Optional) If specified, animation channels will sampled at this rate.

* textureFolder - (Keyword, Optional) Texture files (.jpeg, .tiff etc.) will be created in this folder. If the texture files aren't embeded in the .fbx file, you should place the textures in this folder.

* geometryFolder - (Keyword, Optional) Geometry (.tog) files will be created in this folder. If this option is missing, geometry won't be imported.

* animationFolder - (Keyword, Optional) Animation (.bchan) files will be created in this folder. If this option is missing, animation won't be imported."""
		pass
	pass


class sharedmemoutCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.sharedmemoutCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.sharedmemoutCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class sharedmeminCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.sharedmeminCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.sharedmeminCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class nullCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.nullCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.nullCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class listCOMP(PanelCOMP,COMP,OP):
	""""""
	attribs : td.ListAttribute
	"""The table [[ListAttribute Class|attributes]]. The members of these attributes can be directly written to / updated with new values. Any row/col or cell attributes defined will override these values. Define global per-table attributes here.

```python


n.tableAttribs.fontFace = 'Verdana'

n.tableAttribs.bgColor = (0,0.3,0,1) #dark green background


```
"""
	colAttribs : td.ListAttributes
	"""The set of row [[ListAttributes Class|attributes]]. Accessed by row index.  The members of these attributes can be directly written to / updated with new values and take priority over any attribute members defined a the table level.

```python


n.colAttribs[4].colWidth = 100

n.colAttribs[4].bgColor = (0,0.6,0,1) #highlight entire column in bright green


```
"""
	rowAttribs : td.ListAttributes
	"""The set of row [[ListAttributes Class|attributes]]. Accessed by row index. The members of these attributes can be directly written to / updated with new values and take priority over any attribute members defined a the table level.

```python


n.rowAttribs[3].rowHeight = 50


```
"""
	cellAttribs : td.ListAttributes
	"""The set of cell [[ListAttributes Class|attributes]]. Accessed by row and column. The members of these attributes can be directly written to / updated with new values and take priority over any attribute members defined at the row/col or table level.

```python


n.cellAttribs[3,4].text = 'Fade'

n.cellAttribs[3,4].bgColor = (0.5,0,0,1) #highlight this cell red


```
"""
	displayAttribs : td.ListAttributes
	"""The set of attributes actually displayed in the cell. They are a combination of the cell/row/col/table attributes described above. Accessed by row and column.  When combining attributes, cell attributes take priority over row and column attributes, which themselves take priority over table attributes.

```python
n.displayAttribs[3,4].bgColor #the resulting background color for this specific cell
```
"""
	focusCol : int
	"""Last column with focus for editing."""
	focusRow : int
	"""Last row with focus for editing."""
	radioCol : int
	"""The last selected column."""
	radioRow : int
	"""The last selected row."""
	rolloverCol : int
	"""The last column rolled over."""
	rolloverRow : int
	"""The last row rolled over."""
	selectCol : int
	"""The currently selected column."""
	selectRow : int
	"""The currently selected row."""
	selectionBorderColor : tuple(r, g, b, a)
	"""Get or set the border color for the separate selection, expressed as a 4-tuple, representing its red, green, blue and alpha value."""
	selectionColor : tuple(r, g, b, a)
	"""Get or set the background color for the separate selection, expressed as a 4-tuple, representing its red, green, blue and alpha value."""
	selections : [(startrow, startcol, endrow, endcol), (startrow, startcol, endrow, endcol), ..]
	"""Get or set the row and column coordinates for separate selection formatting, expressed as a list of 4-tuples, each representing startrow, startcol, endrow, endcol."""
	dragRow : int
	"""The currently dragged row."""
	dragCol : int
	"""The currently dragged column."""
	par : parameter.listCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.listCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	def scroll(self, row, col) -> None: 
		"""Scroll List component to the row and column specified.

* row, col - The row and column to scroll to."""
		pass
	def setKeyboardFocus(self, row, col, selectAll=False) -> None: 
		"""Selects and sets the keyboard focus in a cell of the table if the cell is a field.

* row, col -  The row and column of the cell to set the keyboard focus.

* selectAll - (Keyword, Optional) If True, then all text will be selected."""
		pass
	def reset(self, ) -> None: 
		"""Reset the list by running its initialize callbacks."""
		pass
	pass


class lightCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.lightCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.lightCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	def projectionInverse(self, x, y) -> any: 
		"""Returns the inverse projection matrix for the light's view, given the X and Y aspect. In general these would be set to the width and height of your render.

* x - The horizontal aspect ratio.

* y - The vertical aspect ratio."""
		pass
	def projection(self, x, y) -> any: 
		"""Returns the projection [[Matrix Class|matrix]] for the light's view, given the X and Y aspect. In general these would be set to the width and height of your render.

* x - The horizontal aspect ratio.

* y - The vertical aspect ratio.

```python


newlist = op('geo1').pars('t?', 'r?', 's?') # translate/rotate/scale parameters


```"""
		pass
	pass


class handleCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.handleCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.handleCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class geometryCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.geometryCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.geometryCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	def computeBounds(self, display=True, render=True, selected=False, recurse=True) -> any: 
		"""Calculate the bounding box of the child geometry of this component.

A named tuple consisting of (min, max, center, size) is returned. Each component in turn is a named 3-tuple (x, y, z).

* display - (Keyword, Optional) If set to True, only [[SOP Class|SOP operators]] whose[[Display Flag | display flag]] set are included in the calculation.  Furthermore, if the SOP is contained within a child [[geometryCOMP Class|Geometry Component]], that operator must have its display flag set as well.

* render - (Keyword, Optional) If set to True, only [[SOP Class|SOP operators]] whose[[Render Flag | render flag]] set are included in the calculation.  Furthermore, if the SOP is contained within a child [[geometryCOMP Class|Geometry Component]], that operator must have its render flag set as well.

* selected - (Keyword, Optional) If set to True, only child [[COMP Class|components]] that are currently selected are included in the calculation.

* recurse - (Keyword, Optional) If set to True, child components are included in the calculation.

```python


a=op('/project1/geo1').computeBounds()

print(a.min.x)


```"""
		pass
	pass


class fieldCOMP(PanelCOMP,COMP,OP):
	""""""
	par : parameter.fieldCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.fieldCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	def setKeyboardFocus(self, selectAll=False) -> None: 
		"""Set keyboard focus.

* selectAll - (Keyword, Optional) If True, then all text will be selected."""
		pass
	pass


class environmentlightCOMP(ObjectCOMP,COMP,OP):
	""""""
	par : parameter.environmentlightCOMP|parameter.ObjectCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.environmentlightCOMP & parameter.ObjectCOMP & parameter.COMP & parameter.OP"""
	pass


class containerCOMP(PanelCOMP,COMP,OP):
	""""""
	par : parameter.containerCOMP|parameter.PanelCOMP|parameter.COMP|parameter.OP
	"""Parameters of parameter.containerCOMP & parameter.PanelCOMP & parameter.COMP & parameter.OP"""
	def click(self, u, v, clickCount=1, force=False, left=False, middle=False, right=False, group=None) -> None: 
		"""Simulate a mouse click on a container panel at a specific location.

* u - The first coordinate of the click.

* v - The second coordinate of the click.

* clickCount - (Keyword, Optional) If set, it sets the number of clicks. For double clicking etc.

* force - (Keyword, Optional) If set to True, forces the panel click, even when its disabled.

* left,middle,right - (Keyword, Optional) Overrides the default mouse button used.  When none are set, the left mouse button is pressed, and the other buttons are released.

* group - (Keyword, Optional) Specifies an optional panel group name.  See the [[Button COMP]] for a description of group labels.

```python


op('container1').click(0.4, 0.5) # Update U and V


```"""
		pass
	def clickChild(self, childIndex, clickCount=1, force=False, left=False, middle=False, right=False, group=None) -> None: 
		"""Simulate a mouse click of a sub-panel within a container panel.  This can be used to click radio buttons within a single container.

* childIndex - indicates the child panel to click.

* clickCount - (Keyword, Optional) If set, it sets the number of clicks. For double clicking etc.

* force - (Keyword, Optional) If set to True, forces the panel click, even when its disabled.

* left,middle,right - (Keyword, Optional) Overrides the default mouse button used.  When none are set, the left mouse button is pressed, and the other buttons are released.

* group - (Keyword, Optional) Specifies an optional panel group name.  See the [[Button COMP]] for a description of group labels.

```python


op('container1').clickChild(2) # Click the third child panel inside a container.


```"""
		pass
	pass


class compositeTOP(TOP,OP):
	""""""
	par : parameter.compositeTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.compositeTOP & parameter.TOP & parameter.OP"""
	pass


class constantMAT(MAT,OP):
	""""""
	par : parameter.constantMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.constantMAT & parameter.MAT & parameter.OP"""
	pass


class constantTOP(TOP,OP):
	""""""
	par : parameter.constantTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.constantTOP & parameter.TOP & parameter.OP"""
	pass


class convertDAT(DAT,OP):
	""""""
	par : parameter.convertDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.convertDAT & parameter.DAT & parameter.OP"""
	pass


class convertSOP(SOP,OP):
	""""""
	par : parameter.convertSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.convertSOP & parameter.SOP & parameter.OP"""
	pass


class convolveTOP(TOP,OP):
	""""""
	par : parameter.convolveTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.convolveTOP & parameter.TOP & parameter.OP"""
	pass


class copySOP(SOP,OP):
	""""""
	copyIndex : int
	"""The current copy index, beginning at zero."""
	copyTotal : int
	"""The total number of copies."""
	inputPoint : int
	"""The current [[Point Class|point]] being evaluated, of the template."""
	par : parameter.copySOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.copySOP & parameter.SOP & parameter.OP"""
	pass


class cornerpinTOP(TOP,OP):
	""""""
	par : parameter.cornerpinTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.cornerpinTOP & parameter.TOP & parameter.OP"""
	pass


class cplusplusSOP(SOP,OP):
	""""""
	par : parameter.cplusplusSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.cplusplusSOP & parameter.SOP & parameter.OP"""
	pass


class cplusplusTOP(TOP,OP):
	""""""
	par : parameter.cplusplusTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.cplusplusTOP & parameter.TOP & parameter.OP"""
	pass


class creepSOP(SOP,OP):
	""""""
	par : parameter.creepSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.creepSOP & parameter.SOP & parameter.OP"""
	pass


class cropTOP(TOP,OP):
	""""""
	par : parameter.cropTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.cropTOP & parameter.TOP & parameter.OP"""
	pass


class crossTOP(TOP,OP):
	""""""
	par : parameter.crossTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.crossTOP & parameter.TOP & parameter.OP"""
	pass


class cubemapTOP(TOP,OP):
	""""""
	par : parameter.cubemapTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.cubemapTOP & parameter.TOP & parameter.OP"""
	pass


class curveclaySOP(SOP,OP):
	""""""
	par : parameter.curveclaySOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.curveclaySOP & parameter.SOP & parameter.OP"""
	pass


class curvesectSOP(SOP,OP):
	""""""
	par : parameter.curvesectSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.curvesectSOP & parameter.SOP & parameter.OP"""
	pass


class DAT(OP):
	"""A [[DAT]] describes a reference to a DAT operator."""
	export : bool
	"""Get or set [[Export Flag]]"""
	module : module
	"""Retrieve the contents of the DAT as a module. This allows for functions in the module to be called directly. E.g n.module.function(arg1, arg2)"""
	numRows : int
	"""Number of rows in the DAT table."""
	numCols : int
	"""Number of columns in the DAT table."""
	text : str
	"""Get or set contents. Tables are treated as tab delimited columns, newline delimited rows."""
	editingFile : str
	"""The path to the current file used by external editors."""
	isTable : bool
	"""True if the DAT contains table formatted data."""
	isText : bool
	"""True if the DAT contains text formatted data. (ie, not table formatted)."""
	isEditable : bool
	"""True if the DAT contents can be edited (Text DATs, Table DATs, locked DATs etc)."""
	isDAT : bool
	"""True if the operator is a DAT."""
	locals : dict
	"""Local dictionary used during python execution of scripts in this DAT. The dictionary attribute is read only, but not its contents. Its contents may be manipulated directly with scripts, or with an [[Examine DAT]]."""
	jsonObject : dict
	"""Parses the DAT as json and returns a python object."""
	par : parameter.DAT|parameter.OP
	"""Parameters of parameter.DAT & parameter.OP"""
	def run(self, arg1, arg2, *args, endFrame=False, fromOP=None, asParameter=False, group=None, delayFrames=0, delayMilliSeconds=0, delayRef=me) -> any: 
		"""[[Run Class|Run]] the contents of the DAT as a script, returning a Run object which can be used to optionally modify its execution.

* arg - (Optional) Arguments that will be made available to the script in a local tuple named args.

* endFrame - (Keyword, Optional) If set to True, the execution will be delayed until the end of the current frame.

* fromOP - (Keyword, Optional) Specifies an optional [[OP Class|operator]] from which the execution will be run relative to.

* asParameter - (Keyword, Optional) When fromOP used, run relative to a parameter of fromOP.

* group - (Keyword, Optional) Can be used to specify a group label string. This label can then be used with the [[Runs Class|td.runs]] object to modify its execution.

* delayFrames - (Keyword, Optional) Can be used to delay the execution a specific amount of frames.

* delayMilliSeconds - (Keyword, Optional) Can be used to delay the execution a specific amount of milliseconds.  This value is rounded to the nearest frame.

* delayRef - (Keyword, Optional) Specifies an optional [[OP Class|operator]] which is controlled by a different [[Time COMP|Time Component]].  If your own local timeline is paused, you can point to another timeline to ensure this script will still execute for example."""
		pass
	def save(self, filepath, append=False, createFolders=False) -> str: 
		"""Saves the content of the DAT to the file system. Returns the file path that it was saved to.

* filepath - (Optional) The path and filename to save the file to. If this is not given then a default named file will be saved to project.folder

* append - (Keyword, Optional) If set to True and the format is txt, then the contents are appended to the existing file.

* createFolders - (Keyword, Optional) If True, it creates the not existent directories provided by the filepath.

```python


name = n.save() #save in native format with default name

n.save('output.txt') #human readable format without channel names

n.save('C:/Desktop/myFolder/output.txt', createFolders=True)  # supply file path and createFolder flag


```"""
		pass
	def write(self, args) -> str: 
		"""Append content to this DAT. Can also be used to implement DAT printing functions.

```python


# grab DAT

n = op('text1')

# append message directly to DAT

n.write('Hello World')

# use print method

print('Hello World', file=n)


```"""
		pass
	def detectLanguage(self, setLanguage=False) -> str: 
		"""Returns the result of attempting to auto-detect the programming language in the DAT based on the contained text.

* setLanguage - (Keyword, Optional) If True sets the language parameters on the DAT appropriately"""
		pass
	def clear(self, keepSize=False, keepFirstRow=False, keepFirstCol=False) -> None: 
		"""Remove all rows and columns from the table.

* keepSize - (Keyword, Optional) If set to True, size is unchanged, but entries will be set to blank, dependent on other options below.

* keepFirstRow - (Keyword, Optional) If set to True, the first row of cells are retained.

* keepFirstCol - (Keyword, Optional) If set to True, the first column of cells are retained.

```python


n.clear() #remove all rows and columns

n.clear(keepSize=True) #set all table cells to blank

n.clear(keepFirstRow=True) #remove all rows, but keep the first

n.clear(keepFirstRow=True, keepFirstCol=True) #keep the first row, first column, and set remaining cells to blank


```"""
		pass
	def copy(self, DAT) -> None: 
		"""Copy the text or table from the specified [[DAT]] operator.

* OP - The DAT operator whose contents should be copied into the DAT."""
		pass
	def appendRow(self, vals, nameOrIndex, sort=None) -> int: 
		"""Append a row to the end of the table, or after the specified row name/index.  Returns the integer index of the new row.

* vals - (Optional) If specified, will fill the row with the given values. It should be a list of items that can be expressed as strings.  Each item will be copied to one [[Cell Class|cell]].

* nameOrIndex - (Optional) If specified will determine where the new row will be appended. If it's a numeric value it represents the numeric index of the row. If it is a string it represents a row label.

* sort - (Keyword, Optional) If specified will determine the column to keep sorted after the insertion. If it's a numeric value it represents the numeric index of the column. If it is a string it represents a column label.

```python


n.appendRow()

n.appendRow( [1,2,3], 'January' )  #append with values (1,2,3) after the row labelled 'January'

n.appendRow( [1,2,3], 5 )  #append row with values (1,2,3) after the row 5.

n.appendRow( [1,2,3], sort='Month' )  #append row with values (1,2,3) keeping column 'Month' sorted.


```"""
		pass
	def appendRows(self, vals, nameOrIndex, sort=None) -> int: 
		"""Append rows to the end of the table, or after the specified row name/index. Returns the integer of the last row appended.

* vals - (Optional) If specified, will fill the rows with the given values. It should be a list of lists of items that can be expressed as strings.  Each item will be copied to one cell.

* nameOrIndex - (Optional) If specified will determine where the new row will be appended. If it's a numeric value it represents the numeric index of the row. If it is a string it represents a row label.

* sort - (Keyword, Optional) If specified will determine the column to keep sorted after the insertion. If it's a numeric value it represents the numeric index of the column. If it is a string it represents a column label.

```python
n.appendRows()

n.appendRows( [[1,2,3],[4,5,6,7]], 'January' )  #after the row labelled 'January append 2 rows: first one with values (1,2,3), then one with values (4,5,6,7)

n.appendRows( [[1,2,3]], 5 )  # after row 5 append one row with values (1,2,3).

n.appendRows( [1,2,3] )  # append 3 rows with values 1, 2, 3 respectively.
```"""
		pass
	def appendCol(self, vals, nameOrIndex, sort=None) -> int: 
		"""Append a column to the end of the table. See appendRow for similar usage."""
		pass
	def appendCols(self, vals, nameOrIndex, sort=None) -> int: 
		"""Append columns to the end of the table. See appendRows for similar usage."""
		pass
	def insertRow(self, vals, nameOrIndex, sort=None) -> int: 
		"""Insert a row to the beginning of the table or before the specified row name/index.  See DAT.appendRow() for similar usage."""
		pass
	def insertCol(self, vals, nameOrIndex, sort=None) -> int: 
		"""Insert a column to the beginning of the table or before the specified row name/index. See DAT.appendRow() for similar usage."""
		pass
	def replaceRow(self, nameOrIndex, vals, entireRow=True) -> int: 
		"""Replaces the contents of an existing row.

* nameOrIndex - Specifies the row that will be replaced. If it's a numeric value it represents the numeric index of the row. If it is a string it represents a row label.

* vals - (Optional) If specified, will overwrite the row with the given values. It should be a list of lists of items that can be expressed as strings.  Each item will be copied to one cell.

* entireRow - (Keyword, Optional) If True, overwrites every cell in the specified row. If False, will only overwrite as many cells in the row as there are items in vals.

```python


n.replaceRow(0) # will empty all the cells in row 0 (ie. replaced with nothing)

n.replaceRow('January', ['January', 1,2,3])  # the row 'January' will be replaced with the list of 4 items.

n.replaceRow(2, [1,2,3], entireRow=False)  # at row 2 the 3 items will replace the first 3 items in the row.
```"""
		pass
	def replaceCol(self, nameOrIndex, vals, entireCol=True) -> int: 
		"""Replaces the contents of an existing column. See DAT.replaceRow for similar usage."""
		pass
	def deleteRow(self, nameOrIndex) -> None: 
		"""Delete a single row at the specified row name or index.

* nameOrIndex - May be a string for a row name, or numeric index for rowindex."""
		pass
	def deleteRows(self, vals) -> None: 
		"""Deletes multiple rows at the row names or indices specified in vals.

* vals - If specified, will delete each row given. It should be a list of items that can be expressed as strings. If no vals is provided deleteRows does nothing."""
		pass
	def deleteCol(self, nameOrIndex) -> None: 
		"""Delete a single column at the specified column name or index.

* nameOrIndex - May be a string for a column name, or numeric index for column index."""
		pass
	def deleteCols(self, vals) -> None: 
		"""Deletes multiple columns at the column names or indices specified in vals.

* vals - If specified, will delete each column given. It should be a list of items that can be expressed as strings. If no vals is provided deleteCols does nothing."""
		pass
	def setSize(self, numrows, numcols) -> None: 
		"""Set the exact size of the table.

* numrows - The number of rows the table should have.

* numcols - The number of columns the table should have."""
		pass
	def scroll(self, row, col) -> None: 
		"""Bring current DAT viewers to the specified row and column

* row - Row to scroll to.

* col - (Optional) Column to scroll to for tables."""
		pass
	def [rowNameOrIndex, colNameOrIndex] -> any: 
		"""[[Cell Class|cells]] in a table may be accessed with the ```[]``` subscript operator.

The NameOrIndex may be an exact string name, or it may be a numeric index value. [[Pattern Matching]] is ''not'' supported.

* rowNameOrIndex - If a string it specifies a row name, if it's numeric it specifies a row index.

* colNameOrIndex - If a string it specifies a column name, if it's numeric it specifies a column index.

```python


c = n[4, 'June']

c = n[3, 4]


```"""
		pass
	def cell(self, rowNameOrIndex, colNameOrIndex, caseSensitive=True) -> any: 
		"""Find a single [[Cell Class|cell]] in the table, or None if none are found.

* rowNameOrIndex/colNameOrIndex - If a string it specifies a row/column name. If it's numeric it specifies a row/column index. [[Pattern Matching]] is supported for strings.

* caseSensitive - (Optional) Specifies whether or not case sensitivity is used.

```python


c = n.cell(5, 'June') #Return a cell under row 5, column 'June'.

c = n.cell('A* ', 2) #Find a cell under any row beginning with an A, in column 2.


```"""
		pass
	def cells(self, rowNameOrIndex, colNameOrIndex, caseSensitive=True) -> list: 
		"""Returns a (possibly empty) list of [[Cell Class|cells]] that match the given row/column names or indices. See DAT.cell method for similar usage."""
		pass
	def findCell(self, pattern, rows=None, cols=None, valuePattern=True, rowPattern=True, colPattern=True, caseSensitive=False) -> any: 
		"""Returns a cell that matches the given pattern and row/column names or indices or None if no match is found.

* pattern - The pattern to match a cell.

* rows (Keyword, Optional) - If specified, looks for cell only in the specified rows. Must be specified as a list.

* cols (Keyword, Optional) - If specified, looks for cell only in the specified columns. Must be specified as a list.

* valuePattern, rowPattern, colPattern(Keyword, Optional) - If specified and set to False, disables pattern matching for a cell, rows or columns.

* caseSensitive(Keyword, Optional) - Cell matching is case sensitive if set to true.

```python


# given a table 'table1':

# # id # fruit      # color  #

# # 0  # Strawberry # Red    #

# # 1  # Banana     # Yellow #

# # 2  # Cucumber   # Green  #

# # 3  # Blueberry  # Blue   #

# # 4  # Clementine # Orange #

# # 5  # * Fruit     # Green  #



# t is the reference to a table DAT

t = op('/project1/table1')



# search for any cell with the value 'Red'

# will return type:Cell cell:(1, 2) owner:/project1/table1 value:Red

t.findCell('Red')



# search for any cell in the column 'fruit' with a value starting with 'blue'

# will return type:Cell cell:(4, 1) owner:/project1/table1 value:Blueberry

t.findCell('blue* ',cols=['fruit'])



# search for any cell in the column 'fruit' with a value starting with 'blue'

# with case-sensitive search enabled

# will return None

t.findCell('blue* ',cols=['fruit'], caseSensitive=True)



# will return type:Cell cell:(0, 1) owner:/project1/table1 value:fruit

# as the '* ' in the search pattern will be used to pattern match, the

# first row of the second column is matched

t.findCell('* Fruit')



# will return type:Cell cell:(6, 1) owner:/project1/table1 value: * Fruit

# as pattern matching for the search pattern is disabled

# hence the '* ' is not interpreted as a pattern but a string to look for

t.findCell('* Fruit', valuePattern=False)


```"""
		pass
	def findCells(self, pattern, rows=None, cols=None, valuePattern=True, rowPattern=True, colPattern=True) -> list: 
		"""Returns a (possibly empty) list of cells that match the given patterns and row/column names or indices.

* pattern - The pattern to match cells.

* rows (Keyword, Optional) - If specified, looks for cells only in the specified rows.

* cols (Keyword, Optional) - If specified, looks for cells only in the specified columns.

* valuePattern, rowPattern, colPattern(Keyword, Optional) - If specified, overrides pattern matching for cells, rows or columns.

* caseSensitive(Keyword, Optional) - Cell matching is case sensitive if set to true."""
		pass
	def row(self, nameOrIndex1, nameOrIndex2, *args, caseSensitive=True) -> list: 
		"""Returns a list of [[Cell Class|cells]] from the row matching the name/index, or None if nothing is found.

See DAT.col() for similar usage."""
		pass
	def rows(self, nameOrIndex1, nameOrIndex2, *args, caseSensitive=True) -> any: 
		"""Returns a (possibly empty) list of rows (each row being a list of cells). If no arguments are given it returns all rows in the table.

See DAT.rows() for similar usage.

```python


for r in op('table1').rows():

        # do something with row 'r'


```"""
		pass
	def col(self, nameOrIndex1, nameOrIndex2, *args, caseSensitive=True) -> list: 
		"""Returns a list of all the [[Cell Class|cells]] in a column, or None if nothing is found.

* nameOrIndex - If a string it specifies a column name, if it's numeric it specifies a column index. [[Pattern Matching]] is supported.

* caseSensitive - (Optional) Specifies whether or not case sensitivity is used.

```python


r = op('table1').col(3, caseSensitive=False)

r = op('table1').col('June')

r = op('table1').col('A* ', 'B* ') #returns first column beginning with A or B


```"""
		pass
	def cols(self, nameOrIndex1, nameOrIndex2, *args, caseSensitive=True) -> any: 
		"""Returns a (possibly empty) list of columns (each being a list themselves). See DAT.col for similar usage. If no arguments are given then all columns in the table are returned.

* nameOrIndex - (Optional) If a string it specifies a column name, if it's numeric it specifies a column index. [[Pattern Matching]] is supported.

* caseSensitive - (Optional) Specifies whether or not case sensitivity is used.

```python


for c in op('table1').cols():

        # do something with each column 'c'


```"""
		pass
	pass


class xmlDAT(DAT,OP):
	""""""
	par : parameter.xmlDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.xmlDAT & parameter.DAT & parameter.OP"""
	pass


class websocketDAT(DAT,OP):
	""""""
	par : parameter.websocketDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.websocketDAT & parameter.DAT & parameter.OP"""
	def sendText(self, message) -> int: 
		"""Send a text frame over the WebSocket connection.  Returns the number of bytes sent in the message, or a negative value on error.

* message - String content to send.  Multiple string values can be specified, which are joined without spaces.

```python


n = n.sendText('Hello') # send text frame consisting of 'Hello'


```"""
		pass
	def sendPong(self, contents) -> int: 
		"""Send a pong reply over the WebSocket connection.  Returns the number of bytes sent in the message, or a negative value on error.

* contents - (Optional) Binary contents of the frame.  This should match the contents of the original ping request frame. This can include any number of strings, byte arrays, or individual single-byte numeric values.  To serialize non-byte values (example floats or integers) there are several python modules to do this, such as pickle or struct.

```python


n = n.sendPong( 23, 'TYPE', 255, 12, 0x34, b'\\x01\\x00\\x02\\x00\\x03\\x00\\x00\\x00') # send pong reply with specific contents.


```"""
		pass
	def sendPing(self, contents) -> int: 
		"""Send a ping request over the WebSocket connection.  Returns the number of bytes sent in the message, or a negative value on error.

* contents - (Optional) Binary contents of the frame.  This can include any number of strings, byte arrays, or individual single-byte numeric values.  To serialize non-byte values (example floats or integers) there are several python modules to do this, such as pickle or struct.

```python


n = n.sendPing( 23, 'TYPE', 255, 12, 0x34, b'\\x01\\x00\\x02\\x00\\x03\\x00\\x00\\x00') # send ping request with specific contents.


```"""
		pass
	def sendBinary(self, contents) -> int: 
		"""Send a binary frame over the WebSocket connection.  Returns the number of bytes sent in the message, or a negative value on error.

* contents - (Optional) Binary contents of the frame.  This can include any number of strings, byte arrays, or individual single-byte numeric values.  To serialize non-byte values (example floats or integers) there are several python modules to do this, such as pickle or struct.

```python


n = n.sendBinary( 23, 'TYPE', 255, 12, 0x34, b'\\x01\\x00\\x02\\x00\\x03\\x00\\x00\\x00') # send binary frame consisting of various byte values.


```"""
		pass
	pass


class webDAT(DAT,OP):
	""""""
	downloadCurrent : int
	"""Total bytes downloaded so far."""
	downloadFraction : float
	"""Fraction of downloaded size to total size."""
	downloadTotal : int
	"""Total size for download, expressed in bytes."""
	queryContentEncoding : str
	"""Query Content Encoding, as returned from HTML query."""
	queryContentLength : int
	"""Query Content Length, as returned from HTML query."""
	queryContentType : str
	"""Query Content Type, as returned from HTML query."""
	queryContentTypeCharset : str
	"""Query Content Type character set, as returned from HTML query."""
	par : parameter.webDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.webDAT & parameter.DAT & parameter.OP"""
	pass


class udtoutDAT(DAT,OP):
	""""""
	par : parameter.udtoutDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.udtoutDAT & parameter.DAT & parameter.OP"""
	pass


class udtinDAT(DAT,OP):
	""""""
	par : parameter.udtinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.udtinDAT & parameter.DAT & parameter.OP"""
	pass


class udpoutDAT(DAT,OP):
	""""""
	par : parameter.udpoutDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.udpoutDAT & parameter.DAT & parameter.OP"""
	pass


class udpinDAT(DAT,OP):
	""""""
	par : parameter.udpinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.udpinDAT & parameter.DAT & parameter.OP"""
	pass


class tuioinDAT(DAT,OP):
	""""""
	par : parameter.tuioinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.tuioinDAT & parameter.DAT & parameter.OP"""
	pass


class transposeDAT(DAT,OP):
	""""""
	par : parameter.transposeDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.transposeDAT & parameter.DAT & parameter.OP"""
	pass


class touchoutDAT(DAT,OP):
	""""""
	par : parameter.touchoutDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.touchoutDAT & parameter.DAT & parameter.OP"""
	pass


class touchinDAT(DAT,OP):
	""""""
	par : parameter.touchinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.touchinDAT & parameter.DAT & parameter.OP"""
	pass


class textDAT(DAT,OP):
	""""""
	par : parameter.textDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.textDAT & parameter.DAT & parameter.OP"""
	pass


class tcpipDAT(DAT,OP):
	""""""
	par : parameter.tcpipDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.tcpipDAT & parameter.DAT & parameter.OP"""
	def sendBytes(self, message1, message2, *args) -> int: 
		"""Send one or more sequence of bytes. No terminators are appended.

* message - Messages can any combination of strings, byte arrays, or individual single-byte numeric values. To serialize non-byte values (example floats or integers) there are several python modules such as pickle or struct.

```python


n.sendBytes( 'TYPE', 23, 255, 12, 0x34, b'\x01\x00\x02\x00\x03\x00\x00\x00' )


```"""
		pass
	def send(self, message1, message2, *args , terminator=' ') -> int: 
		"""Send a sequence of strings through this connection.

* message - One or more strings to send.

* terminator - (Keyword, Optional) Specifies how the message is to be terminated. IIf no append terminator is specified, a null character will automatically be appended to the message. To send no terminator, use terminator=''.

The number of bytes sent is returned.

```python


n.send('Hello', 'World',  terminator='\r\n') # send two strings with windows style newline termination.


```"""
		pass
	pass


class tableDAT(DAT,OP):
	""""""
	subRow : int
	"""Current row index for Table expressions."""
	subCol : int
	"""Current col index for Table expressions."""
	fillName : string
	"""Current header name for Table expressions."""
	par : parameter.tableDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.tableDAT & parameter.DAT & parameter.OP"""
	pass


class switchDAT(DAT,OP):
	""""""
	par : parameter.switchDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.switchDAT & parameter.DAT & parameter.OP"""
	pass


class substituteDAT(DAT,OP):
	""""""
	inputCell : Cell
	"""The current input [[Cell Class|cell]] being evaluated. From the [[Cell Class|cell]] you can get its row, column and value. e.g. me.inputCell.val or use the specific members listed below."""
	inputCol : Col
	"""The current input colunn being evaluated."""
	inputRow : Row
	"""The current input row being evaluated."""
	inputTable : OP
	"""The current input [[DAT Class|DAT]] being evaluated.

```python


me.inputCell.val # value in cell

me.inputTable[2,3].val # cell row 2, column 3

me.inputTable[me.inputRow, me.inputCol-1].val # cell in previous column

me.inputCell.offset(0, -1) # alternative syntax for previous column


```
"""
	par : parameter.substituteDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.substituteDAT & parameter.DAT & parameter.OP"""
	pass


class sortDAT(DAT,OP):
	""""""
	par : parameter.sortDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.sortDAT & parameter.DAT & parameter.OP"""
	pass


class soptoDAT(DAT,OP):
	""""""
	par : parameter.soptoDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.soptoDAT & parameter.DAT & parameter.OP"""
	pass


class serialDAT(DAT,OP):
	""""""
	par : parameter.serialDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.serialDAT & parameter.DAT & parameter.OP"""
	def sendBytes(self, message1, message2, *args) -> int: 
		"""Send one or more sequence of bytes. No terminators are appended.

* message - Messages can any combination of strings, byte arrays, or individual single-byte numeric values. To serialize non-byte values (example floats or integers) there are several python modules such as pickle or struct.

```python


n.sendBytes( 'TYPE', 23, 255, 12, 0x34, b'\x01\x00\x02\x00\x03\x00\x00\x00' )


```"""
		pass
	def send(self, message1, message2, *args , terminator=' ') -> int: 
		"""Send a sequence of strings through this connection.

* message - One or more strings to write into the file.

* terminator - (Keyword, Optional) Specifies how the message is to be terminated. If no append terminator is specified, a null character will automatically be appended to the message. To send no terminator, use terminator=''.

The number of bytes sent is returned.

```python


n.send('Hello', 'World',  terminator='\r\n') #send two strings with windows style newline termination.


```"""
		pass
	pass


class selectDAT(DAT,OP):
	""""""
	inputCell : Cell
	"""The current input [[Cell Class|cell]] being evaluated. From the [[Cell Class|cell]] you can get its row, column and value. e.g. me.inputCell.val or use the specific members listed below."""
	inputCol : Col
	"""The current input column being evaluated."""
	inputRow : Row
	"""The current input row being evaluated."""
	inputTable : OP
	"""The current input [[DAT Class|DAT]] being evaluated.

```python


me.inputCell.val #value in cell

me.inputTable[2,3].val #cell row 2, column 3

me.inputTable[me.inputRow, me.inputCol-1].val #cell in previous column

me.inputCell.offset(0, -1) #alternative syntax for previous column


```
"""
	par : parameter.selectDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.selectDAT & parameter.DAT & parameter.OP"""
	pass


class scriptDAT(DAT,OP):
	""""""
	par : parameter.scriptDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.scriptDAT & parameter.DAT & parameter.OP"""
	def appendCustomPage(self, name) -> Page: 
		"""Add a new [[Page Class|page]] of custom parameters. See [[Page Class]] for more details.

```python


page = scriptOp.appendCustomPage('Custom1')

page.appendFloat('X1')


```"""
		pass
	def destroyCustomPars(self, ) -> any: 
		"""Remove all custom parameters from COMP."""
		pass
	def sortCustomPages(self, page1, page2, page3, *args) -> None: 
		"""Reorder custom parameter pages.

```python


scriptOp.sortCustomPages('Definition','Controls')


```"""
		pass
	pass


class reorderDAT(DAT,OP):
	""""""
	par : parameter.reorderDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.reorderDAT & parameter.DAT & parameter.OP"""
	pass


class performDAT(DAT,OP):
	""""""
	par : parameter.performDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.performDAT & parameter.DAT & parameter.OP"""
	pass


class parameterexecuteDAT(DAT,OP):
	""""""
	par : parameter.parameterexecuteDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.parameterexecuteDAT & parameter.DAT & parameter.OP"""
	pass


class panelexecuteDAT(DAT,OP):
	""""""
	par : parameter.panelexecuteDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.panelexecuteDAT & parameter.DAT & parameter.OP"""
	pass


class outDAT(DAT,OP):
	""""""
	par : parameter.outDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.outDAT & parameter.DAT & parameter.OP"""
	pass


class oscoutDAT(DAT,OP):
	""""""
	par : parameter.oscoutDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.oscoutDAT & parameter.DAT & parameter.OP"""
	pass


class oscinDAT(DAT,OP):
	""""""
	par : parameter.oscinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.oscinDAT & parameter.DAT & parameter.OP"""
	pass


class opfindDAT(DAT,OP):
	""""""
	par : parameter.opfindDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.opfindDAT & parameter.DAT & parameter.OP"""
	pass


class opexecuteDAT(DAT,OP):
	""""""
	par : parameter.opexecuteDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.opexecuteDAT & parameter.DAT & parameter.OP"""
	pass


class nullDAT(DAT,OP):
	""""""
	par : parameter.nullDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.nullDAT & parameter.DAT & parameter.OP"""
	pass


class multitouchinDAT(DAT,OP):
	""""""
	par : parameter.multitouchinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.multitouchinDAT & parameter.DAT & parameter.OP"""
	pass


class mqttclientDAT(DAT,OP):
	""""""
	isConnected : bool
	"""Return True if connected to a broker, and False if not."""
	par : parameter.mqttclientDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.mqttclientDAT & parameter.DAT & parameter.OP"""
	def publish(self, topic, payload, qos=0, retain=False) -> None: 
		"""Publish content to a specific topic.

* topic - The topic to publish to.

* payload - The actual message to send.

* qos - (Keyword, Optional) The quality of service level to use.

* retain - (Keyword, Optional) If set to True, the message will be set as the 'last known good'retained message for the topic.

```python


n.publish('temperature', b'23')


```"""
		pass
	def subscribe(self, topic, qos=0) -> None: 
		"""Subscribe to a specific topic from the broker.

* topic - The topic to subscribe to. Multiple topics can be subscribed to at once by providing a list.

* qos - (Keyword, Optional) Quality of Service for delivery: At most once (0), At least once (1) or Exactly once (2).

```python


n.subscribe('weather')


```"""
		pass
	def unsubscribe(self, topic) -> None: 
		"""Unsubscribe from a previously subscribed topic.

* topic - The topic to unsubscribe from.  Multiple topics can be unsubscribed from at once by providing a list.

```python


n.unsubscribe('weather')


```"""
		pass
	pass


class monitorsDAT(DAT,OP):
	""""""
	par : parameter.monitorsDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.monitorsDAT & parameter.DAT & parameter.OP"""
	pass


class midiinDAT(DAT,OP):
	""""""
	par : parameter.midiinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.midiinDAT & parameter.DAT & parameter.OP"""
	pass


class midieventDAT(DAT,OP):
	""""""
	par : parameter.midieventDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.midieventDAT & parameter.DAT & parameter.OP"""
	pass


class mergeDAT(DAT,OP):
	""""""
	par : parameter.mergeDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.mergeDAT & parameter.DAT & parameter.OP"""
	pass


class keyboardinDAT(DAT,OP):
	""""""
	par : parameter.keyboardinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.keyboardinDAT & parameter.DAT & parameter.OP"""
	pass


class insertDAT(DAT,OP):
	""""""
	subRow : int
	"""Current row index for Insert DAT Table expressions."""
	subCol : int
	"""Current col index for Insert DAT Table expressions."""
	fillName : str
	"""Current header name for Insert DAT Table expressions."""
	par : parameter.insertDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.insertDAT & parameter.DAT & parameter.OP"""
	pass


class infoDAT(DAT,OP):
	""""""
	par : parameter.infoDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.infoDAT & parameter.DAT & parameter.OP"""
	pass


class indicesDAT(DAT,OP):
	""""""
	par : parameter.indicesDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.indicesDAT & parameter.DAT & parameter.OP"""
	pass


class inDAT(DAT,OP):
	""""""
	par : parameter.inDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.inDAT & parameter.DAT & parameter.OP"""
	pass


class folderDAT(DAT,OP):
	""""""
	par : parameter.folderDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.folderDAT & parameter.DAT & parameter.OP"""
	pass


class fileoutDAT(DAT,OP):
	""""""
	writeCount : int
	"""The number of times data has been written. This can be used to create an incrementing filename."""
	par : parameter.fileoutDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.fileoutDAT & parameter.DAT & parameter.OP"""
	def sendBytes(self, message1, message2, *args) -> int: 
		"""Write one or more sequence of bytes. No terminators are appended.

* message - Messages can any combination of strings, byte arrays, or individual single-byte numeric values. To serialize non-byte values (example floats or integers) there are several python modules such as pickle or struct.

```python


n.sendBytes( 'TYPE', 23, 255, 12, 0x34, b'\x01\x00\x02\x00\x03\x00\x00\x00' )


```"""
		pass
	def send(self, message1, message2, *args , terminator=' ') -> int: 
		"""Used to write strings into the file.

* message - One or more strings to write into the file.

* terminator - (Keyword, Optional) Specifies how the message is to be terminated. If no append terminator is specified, a null character will automatically be appended to the message. To send no terminator, use terminator=''.

The number of bytes sent is returned.

```python


n.send('Hello', 'World',  terminator='\r\n') # send two strings with windows style newline termination.


```"""
		pass
	pass


class fileinDAT(DAT,OP):
	""""""
	par : parameter.fileinDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.fileinDAT & parameter.DAT & parameter.OP"""
	pass


class fifoDAT(DAT,OP):
	""""""
	par : parameter.fifoDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.fifoDAT & parameter.DAT & parameter.OP"""
	pass


class executeDAT(DAT,OP):
	""""""
	par : parameter.executeDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.executeDAT & parameter.DAT & parameter.OP"""
	pass


class examineDAT(DAT,OP):
	""""""
	par : parameter.examineDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.examineDAT & parameter.DAT & parameter.OP"""
	pass


class evaluateDAT(DAT,OP):
	""""""
	exprCell : any
	"""The current expression [[Cell Class|cell]] being evaluated.  From the [[Cell Class|cell]] you can get its row, column and value. e.g. me.exprCell.val or use the specific members listed below.  Too see how a [[Cell Class]] such as me.exprCell is automatically converted to a string or number in an expression see [[Cell Class#Casting to a Value|Casting to a Value]]."""
	exprCol : any
	"""The current expression column being evaluated."""
	exprRow : any
	"""The current expression row being evaluated."""
	exprTable : any
	"""The input [[DAT Class|DAT]] containing the expressions."""
	inputCell : any
	"""The current input [[Cell Class|cell]] being evaluated. From the [[Cell Class|cell]] you can get its row, column and value. e.g. me.inputCell.val or use the specific members listed below.  To see how a [[Cell Class]] such as me.inputCell is automatically converted to a string or number in an expression see [[Cell Class#Casting to a Value|Casting to a Value]]."""
	inputCol : any
	"""The current input column being evaluated."""
	inputRow : any
	"""The current input row being evaluated."""
	inputTable : any
	"""The input [[DAT Class|DAT]] containing the source values."""
	par : parameter.evaluateDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.evaluateDAT & parameter.DAT & parameter.OP"""
	pass


class etherdreamDAT(DAT,OP):
	""""""
	par : parameter.etherdreamDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.etherdreamDAT & parameter.DAT & parameter.OP"""
	pass


class errorDAT(DAT,OP):
	""""""
	par : parameter.errorDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.errorDAT & parameter.DAT & parameter.OP"""
	pass


class datexecuteDAT(DAT,OP):
	""""""
	par : parameter.datexecuteDAT|parameter.DAT|parameter.OP
	"""Parameters of parameter.datexecuteDAT & parameter.DAT & parameter.OP"""
	pass


class dattoSOP(SOP,OP):
	""""""
	par : parameter.dattoSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.dattoSOP & parameter.SOP & parameter.OP"""
	pass


class deformSOP(SOP,OP):
	""""""
	par : parameter.deformSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.deformSOP & parameter.SOP & parameter.OP"""
	pass


class deleteSOP(SOP,OP):
	""""""
	inputPoint : int
	"""The current [[Point Class|point]] being evaluated. Can only be used in the parameters for this SOP."""
	inputPrim : int
	"""The current [[Prim Class|primitive]] being evaluated. Can only be used in the parameters for this SOP."""
	par : parameter.deleteSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.deleteSOP & parameter.SOP & parameter.OP"""
	pass


class depthMAT(MAT,OP):
	""""""
	par : parameter.depthMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.depthMAT & parameter.MAT & parameter.OP"""
	pass


class depthTOP(TOP,OP):
	""""""
	par : parameter.depthTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.depthTOP & parameter.TOP & parameter.OP"""
	pass


class differenceTOP(TOP,OP):
	""""""
	par : parameter.differenceTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.differenceTOP & parameter.TOP & parameter.OP"""
	pass


class directxinTOP(TOP,OP):
	""""""
	par : parameter.directxinTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.directxinTOP & parameter.TOP & parameter.OP"""
	pass


class directxoutTOP(TOP,OP):
	""""""
	par : parameter.directxoutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.directxoutTOP & parameter.TOP & parameter.OP"""
	pass


class displaceTOP(TOP,OP):
	""""""
	par : parameter.displaceTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.displaceTOP & parameter.TOP & parameter.OP"""
	pass


class divideSOP(SOP,OP):
	""""""
	par : parameter.divideSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.divideSOP & parameter.SOP & parameter.OP"""
	pass


class edgeTOP(TOP,OP):
	""""""
	par : parameter.edgeTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.edgeTOP & parameter.TOP & parameter.OP"""
	pass


class embossTOP(TOP,OP):
	""""""
	par : parameter.embossTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.embossTOP & parameter.TOP & parameter.OP"""
	pass


class extrudeSOP(SOP,OP):
	""""""
	par : parameter.extrudeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.extrudeSOP & parameter.SOP & parameter.OP"""
	pass


class facetSOP(SOP,OP):
	""""""
	par : parameter.facetSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.facetSOP & parameter.SOP & parameter.OP"""
	pass


class feedbackTOP(TOP,OP):
	""""""
	par : parameter.feedbackTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.feedbackTOP & parameter.TOP & parameter.OP"""
	pass


class fileinSOP(SOP,OP):
	""""""
	par : parameter.fileinSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.fileinSOP & parameter.SOP & parameter.OP"""
	pass


class filletSOP(SOP,OP):
	""""""
	par : parameter.filletSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.filletSOP & parameter.SOP & parameter.OP"""
	pass


class fitSOP(SOP,OP):
	""""""
	par : parameter.fitSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.fitSOP & parameter.SOP & parameter.OP"""
	pass


class fitTOP(TOP,OP):
	""""""
	par : parameter.fitTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.fitTOP & parameter.TOP & parameter.OP"""
	pass


class flipTOP(TOP,OP):
	""""""
	par : parameter.flipTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.flipTOP & parameter.TOP & parameter.OP"""
	pass


class fontSOP(SOP,OP):
	""""""
	par : parameter.fontSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.fontSOP & parameter.SOP & parameter.OP"""
	pass


class forceSOP(SOP,OP):
	""""""
	par : parameter.forceSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.forceSOP & parameter.SOP & parameter.OP"""
	pass


class fractalSOP(SOP,OP):
	""""""
	par : parameter.fractalSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.fractalSOP & parameter.SOP & parameter.OP"""
	pass


class glslMAT(MAT,OP):
	""""""
	compileResult : str
	"""The latest compile result."""
	par : parameter.glslMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.glslMAT & parameter.MAT & parameter.OP"""
	pass


class glslmultiTOP(TOP,OP):
	""""""
	compileResult : str
	"""The latest compile result."""
	par : parameter.glslmultiTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.glslmultiTOP & parameter.TOP & parameter.OP"""
	pass


class glslTOP(TOP,OP):
	""""""
	compileResult : str
	"""The latest compile result."""
	par : parameter.glslTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.glslTOP & parameter.TOP & parameter.OP"""
	pass


class gridSOP(SOP,OP):
	""""""
	par : parameter.gridSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.gridSOP & parameter.SOP & parameter.OP"""
	pass


class groupSOP(SOP,OP):
	""""""
	inputPoint : Point
	"""The current [[Point Class|point]] being evaluated."""
	inputPrim : Prim
	"""The current [[Prim Class|primitive]] being evaluated."""
	par : parameter.groupSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.groupSOP & parameter.SOP & parameter.OP"""
	pass


class holeSOP(SOP,OP):
	""""""
	par : parameter.holeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.holeSOP & parameter.SOP & parameter.OP"""
	pass


class hsvadjustTOP(TOP,OP):
	""""""
	par : parameter.hsvadjustTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.hsvadjustTOP & parameter.TOP & parameter.OP"""
	pass


class hsvtorgbTOP(TOP,OP):
	""""""
	par : parameter.hsvtorgbTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.hsvtorgbTOP & parameter.TOP & parameter.OP"""
	pass


class inMAT(MAT,OP):
	""""""
	par : parameter.inMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.inMAT & parameter.MAT & parameter.OP"""
	pass


class insideTOP(TOP,OP):
	""""""
	par : parameter.insideTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.insideTOP & parameter.TOP & parameter.OP"""
	pass


class inSOP(SOP,OP):
	""""""
	par : parameter.inSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.inSOP & parameter.SOP & parameter.OP"""
	pass


class inTOP(TOP,OP):
	""""""
	par : parameter.inTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.inTOP & parameter.TOP & parameter.OP"""
	pass


class inversecurveSOP(SOP,OP):
	""""""
	par : parameter.inversecurveSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.inversecurveSOP & parameter.SOP & parameter.OP"""
	pass


class isosurfaceSOP(SOP,OP):
	""""""
	curPos : any
	"""The current [[Position Class|position]] of the surface."""
	par : parameter.isosurfaceSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.isosurfaceSOP & parameter.SOP & parameter.OP"""
	pass


class joinSOP(SOP,OP):
	""""""
	par : parameter.joinSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.joinSOP & parameter.SOP & parameter.OP"""
	pass


class jointSOP(SOP,OP):
	""""""
	par : parameter.jointSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.jointSOP & parameter.SOP & parameter.OP"""
	pass


class kinectSOP(SOP,OP):
	""""""
	par : parameter.kinectSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.kinectSOP & parameter.SOP & parameter.OP"""
	pass


class kinectTOP(TOP,OP):
	""""""
	par : parameter.kinectTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.kinectTOP & parameter.TOP & parameter.OP"""
	pass


class latticeSOP(SOP,OP):
	""""""
	par : parameter.latticeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.latticeSOP & parameter.SOP & parameter.OP"""
	pass


class layoutTOP(TOP,OP):
	""""""
	par : parameter.layoutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.layoutTOP & parameter.TOP & parameter.OP"""
	pass


class leapmotionTOP(TOP,OP):
	""""""
	par : parameter.leapmotionTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.leapmotionTOP & parameter.TOP & parameter.OP"""
	pass


class levelTOP(TOP,OP):
	""""""
	par : parameter.levelTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.levelTOP & parameter.TOP & parameter.OP"""
	pass


class limitSOP(SOP,OP):
	""""""
	par : parameter.limitSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.limitSOP & parameter.SOP & parameter.OP"""
	pass


class lineSOP(SOP,OP):
	""""""
	par : parameter.lineSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.lineSOP & parameter.SOP & parameter.OP"""
	pass


class linethickSOP(SOP,OP):
	""""""
	par : parameter.linethickSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.linethickSOP & parameter.SOP & parameter.OP"""
	pass


class lodSOP(SOP,OP):
	""""""
	par : parameter.lodSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.lodSOP & parameter.SOP & parameter.OP"""
	pass


class lookupTOP(TOP,OP):
	""""""
	par : parameter.lookupTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.lookupTOP & parameter.TOP & parameter.OP"""
	pass


class lsystemSOP(SOP,OP):
	""""""
	par : parameter.lsystemSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.lsystemSOP & parameter.SOP & parameter.OP"""
	pass


class lumablurTOP(TOP,OP):
	""""""
	par : parameter.lumablurTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.lumablurTOP & parameter.TOP & parameter.OP"""
	pass


class lumalevelTOP(TOP,OP):
	""""""
	par : parameter.lumalevelTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.lumalevelTOP & parameter.TOP & parameter.OP"""
	pass


class magnetSOP(SOP,OP):
	""""""
	par : parameter.magnetSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.magnetSOP & parameter.SOP & parameter.OP"""
	pass


class MAT(OP):
	"""A [[MAT]] describes a reference to a MAT operator."""
	isMAT : bool
	"""True if the operator is a Material."""
	par : parameter.MAT|parameter.OP
	"""Parameters of parameter.MAT & parameter.OP"""
	pass


class wireframeMAT(MAT,OP):
	""""""
	par : parameter.wireframeMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.wireframeMAT & parameter.MAT & parameter.OP"""
	pass


class switchMAT(MAT,OP):
	""""""
	par : parameter.switchMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.switchMAT & parameter.MAT & parameter.OP"""
	pass


class selectMAT(MAT,OP):
	""""""
	par : parameter.selectMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.selectMAT & parameter.MAT & parameter.OP"""
	pass


class pointspriteMAT(MAT,OP):
	""""""
	par : parameter.pointspriteMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.pointspriteMAT & parameter.MAT & parameter.OP"""
	pass


class phongMAT(MAT,OP):
	""""""
	par : parameter.phongMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.phongMAT & parameter.MAT & parameter.OP"""
	pass


class pbrMAT(MAT,OP):
	""""""
	par : parameter.pbrMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.pbrMAT & parameter.MAT & parameter.OP"""
	pass


class outMAT(MAT,OP):
	""""""
	par : parameter.outMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.outMAT & parameter.MAT & parameter.OP"""
	pass


class nullMAT(MAT,OP):
	""""""
	par : parameter.nullMAT|parameter.MAT|parameter.OP
	"""Parameters of parameter.nullMAT & parameter.MAT & parameter.OP"""
	pass


class materialSOP(SOP,OP):
	""""""
	par : parameter.materialSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.materialSOP & parameter.SOP & parameter.OP"""
	pass


class mathTOP(TOP,OP):
	""""""
	par : parameter.mathTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.mathTOP & parameter.TOP & parameter.OP"""
	pass


class matteTOP(TOP,OP):
	""""""
	par : parameter.matteTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.matteTOP & parameter.TOP & parameter.OP"""
	pass


class mergeSOP(SOP,OP):
	""""""
	par : parameter.mergeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.mergeSOP & parameter.SOP & parameter.OP"""
	pass


class Mesh(Prim):
	"""A Mesh describes an instance of a single [[Mesh|geometry mesh]].  It is an instance of a [[Prim Class]]."""
	closedU : bool
	"""Returns True if the mesh is closed in U, False otherwise."""
	closedV : bool
	"""Returns True if the mesh is closed in V, False otherwise."""
	numRows : int
	"""Number of rows in the mesh."""
	numCols : int
	"""Number of columns in the mesh."""
	par : parameter.Mesh|parameter.Prim
	"""Parameters of parameter.Mesh & parameter.Prim"""
	pass


class metaballSOP(SOP,OP):
	""""""
	par : parameter.metaballSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.metaballSOP & parameter.SOP & parameter.OP"""
	pass


class mirrorTOP(TOP,OP):
	""""""
	par : parameter.mirrorTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.mirrorTOP & parameter.TOP & parameter.OP"""
	pass


class modelSOP(SOP,OP):
	""""""
	par : parameter.modelSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.modelSOP & parameter.SOP & parameter.OP"""
	def appendPoint(self, ) -> Point: 
		"""Append a [[Point Class|point]] to this SOP. The appended point will be returned."""
		pass
	def appendPoly(self, numVertices, closed=True, addPoints=True) -> Poly: 
		"""Append a [[Poly Class|poly]] to this SOP. Returns the appended polygon.

*  numVertices - Specifies the initial number of [[Vertex Class|vertices]].

*  closed - (Keyword, Optional) Specifies whether or not the last [[Vertex Class|vertex]] of the polygon will connect to the first. An open polygon will be drawn as a line.

*  addPoints - (Keyword, Optional) If True, a new [[Point Class|point]] will be attached to each [[Vertex Class|vertex]], otherwise the [[Vertex Class|vertex]] point references will need to be manually set afterwards. Use this option when creating [[Poly Class|polygons]] with shared [[Vertex Class|vertices]]."""
		pass
	def appendBezier(self, numVertices, closed=False, order=4, addPoints=True) -> Bezier: 
		"""Append a [[Bezier Class|Bezier]] to this SOP. Returns the appended Bezier.

*  numVertices - Specifies the initial number of [[Vertex Class|vertices]].  The number of [[Vertex Class|vertices]] '''must''' correspond to the order (degree-1) and closed/open state of the curve.  For closed curves, the number of vertices must be a multiple of the degree.  For open curves, it must be one more than a multiple of the degree.

```python


n.appendBezier(6, closed=True) #closed, cubic, 6 vertices, or 2 spans


```


```python


n.appendBezier(7) #open, cubic, 7 vertices, or 2 spans


```


*  closed - (Keyword, Optional) Specifies whether or not the last [[Vertex Class|vertex]] of the curve will connect to the first. An open Bezier will be drawn as a line.

*  order - (Keyword, Optional) Specifies the degree of the Bezier. By default it creates cubic (order=4) Beziers.

*  addPoints - (Keyword, Optional) If True, a new [[Point Class|point]] will be attached to each [[Vertex Class|vertex]], otherwise the [[Vertex Class|vertex]] point references will need to be manually set afterwards. Use this option when creating Beziers with shared vertices."""
		pass
	def appendMesh(self, numRows, numCols, closedU=False, closedV=False, addPoints=True) -> Mesh: 
		"""Append a [[Mesh Class|mesh]] to this SOP. Returns the appended mesh.

*  numRows, numCols - Specifies the initial number of rows and columns.

*  closedU - (Keyword, Optional) Specifies whether or not the grid is wrapped in the u direction.

*  closedV - (Keyword, Optional) Specifies whether or not the grid is wrapped in the v direction.

*  addPoints - (Keyword, Optional) If True, a new [[Point Class|point]] will be attached to each [[Vertex Class|vertex]], otherwise the [[Vertex Class|vertex]] point references will need to be manually set afterwards. Use this option when creating [[Mesh Class|meshes]] with shared [[Vertex Class|vertices]]."""
		pass
	def clear(self, ) -> None: 
		"""Remove all geometry."""
		pass
	def copy(self, sop) -> None: 
		"""Copy geometry from the specified [[SOP]] operator.

*  sop - The SOP to copy geometry from. Geometry currently in this SOP will be removed."""
		pass
	pass


class monochromeTOP(TOP,OP):
	""""""
	par : parameter.monochromeTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.monochromeTOP & parameter.TOP & parameter.OP"""
	pass


class moviefileinTOP(TOP,OP):
	""""""
	fileHeight : int
	"""Height of the movie, in pixels."""
	fileWidth : int
	"""Width of the movie, in pixels."""
	hasAudio : bool
	"""True if the movie contains audio."""
	hasDecodeErrors : bool
	"""True if any frames failed to decode, likely due to file corruption. Currently only works on Hap codec files."""
	index : float
	"""Current movie index."""
	indexFraction : float
	"""Current movie index expressed as a fraction of total length."""
	isFullyPreRead : bool
	"""True if the movie has pre-read all of its Pre-Read frames and is ready to play. For single images this is true when the image is ready to be shown. When a movie is playing, this member will flip between True and False as its pre-read frames get consumed/refilled. When a movie isn't playing forward, this member can tell you if the movie is in an optimal state to start playing back from its currently selected frame/cued frame."""
	isInvalid : bool
	"""True if the movie has failed to load."""
	isLastFrame : bool
	"""True if the movie is currently showing its last frame."""
	isLoopFrame : bool
	"""True if the movie has just looped and is showing the first frame after a loop."""
	isOddField : bool
	"""True if the current displayed de-interlaced frame is the odd field."""
	isOpen : bool
	"""True if the file has been opened."""
	isOpening : bool
	"""True when the file is opening."""
	isFileOpening : bool
	"""Returns true while the file header is being read."""
	isPreloading : bool
	"""True when the file is preloading."""
	lastIndexUploaded : float
	"""The index of the if the last frame uploaded to the GPU."""
	numHeaders : int
	"""Returns the number of key-value pairs in the file's header."""
	numImages : float
	"""The number of images in the movie."""
	numSeconds : float
	"""The number of seconds in the movie."""
	rate : float
	"""The movie sample rate."""
	sourceChannels : tuple
	"""A list of the available channels in the file e.g. R, G, B, A for typical color images."""
	start : float
	"""The start index of the movie."""
	trueIndex : float
	"""The actual current index of the movie, disregarding trimming and other options."""
	trueNumImages : float
	"""The actual number of images contained in the movie, not affected by trimming."""
	par : parameter.moviefileinTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.moviefileinTOP & parameter.TOP & parameter.OP"""
	def findHeader(self, key) -> any: 
		"""Returns the value of the header with the given key. This method will return a blank string if the header is not found.

* key - The name of the header to search for."""
		pass
	def getHeader(self, index) -> tuple: 
		"""Returns a tuple with the key and value of the header at the given index. This method will throw an error if the index is not valid. The numHeaders member can be used to get the number of valid headers in the file.

* index - The index of the header to search for starting with 0."""
		pass
	def unload(self, cacheMemory=False) -> None: 
		"""Unloads the movie and frees its memory usage. The movie will open again next time it cooks, so make sure nothing is still using it to keep it closed.

* cacheMemory - (Keyword, Optional) If you are preloading into a Movie File In TOP that already has video, and the video format/resolution is the same, you can use the cacheMemory option to first unload the original movie and cache its memory, avoiding a reallocation when the preload() occurs. If True the memory (textures, upload buffers) of the movie will be cached for use by another movie later on. Useful if you are opening/closing many movies with the same codec and resolution."""
		pass
	def preload(self, index) -> None: 
		"""Preloads the movie by opening it and pre-reading the first frames. Use the isFullyPreRead member to see if it's ready to play. This is done in a way to minimize impact on the existing playback of the application. If movies are being loaded on startup it's better to just call cook() on the Movie File In TOP instead of preload() since cook() will be more thorough.

* index - (Optional) If specified the movie will be opened at the specified frame index. If not, then the movie will be opened at the index specified by its parameters."""
		pass
	pass


class moviefileoutTOP(TOP,OP):
	""""""
	writeCount : any
	"""The number of files that have been written. This can be used to create an incrementing file name."""
	curSeqIndex : any
	"""The current index of the last written image on disk."""
	fileSuffix : str
	"""Returns the generated file suffix. It will be generated based on the values of the parameters Unique Suffix and N, plus the file extension. It will take one of two forms: ```''N''.''ext''</code> or <code>''N''.''i''.''ext''</code> where <code>''N''</code> is the suffix index (uniquely generated if Unique Suffix is enabled), <code>''i''</code> is the image sequence index (used only for the image sequence type), and <code>''ext''``` is the image/movie extension."""
	par : parameter.moviefileoutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.moviefileoutTOP & parameter.TOP & parameter.OP"""
	pass


class multiplyTOP(TOP,OP):
	""""""
	par : parameter.multiplyTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.multiplyTOP & parameter.TOP & parameter.OP"""
	pass


class ndiinTOP(TOP,OP):
	""""""
	par : parameter.ndiinTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.ndiinTOP & parameter.TOP & parameter.OP"""
	pass


class ndioutTOP(TOP,OP):
	""""""
	par : parameter.ndioutTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.ndioutTOP & parameter.TOP & parameter.OP"""
	pass


class NetworkEditor(Pane):
	"""The NetworkEditor class describes an instance of a [[Network Editor]]. They are subclasses of the [[Pane Class]], which can be accessed from the [[UI Class|ui]] object."""
	showBackdropCHOPs : bool
	"""Enable or disable [[CHOP]] viewers as backdrops."""
	showBackdropGeometry : bool
	"""Enable or disable [[SOP]] and [[Geometry Object|Geometry object]] viewers as backdrops."""
	showBackdropTOPs : bool
	"""Enable or disable [[TOP]] viewers as backdrops."""
	showColorPalette : bool
	"""Enable or disable display of the operator color palette selector."""
	showDataLinks : bool
	"""Enable or disable disable of operator data links."""
	showList : bool
	"""Control display of operators as a list, or connected nodes."""
	showNetworkOverview : bool
	"""Enable or disable display of the network overview."""
	showParameters : bool
	"""Enable or disable display of the currently selected operator parameters."""
	straightLinks : bool
	"""Control display of operator links as straight or curved."""
	x : float
	"""Get or set the x coordinate of the network editor area,  where 1 unit = 1 pixel when zoom = 1."""
	y : float
	"""Get or set the y coordinate of the network editor area, where 1 unit = 1 pixel when zoom = 1."""
	zoom : float
	"""Get or set the zoom factor of the network editor area, where a zoom factor of 1 draws each node at its unscaled resolution."""
	par : parameter.NetworkEditor|parameter.Pane
	"""Parameters of parameter.NetworkEditor & parameter.Pane"""
	def fitWidth(self, width) -> None: 
		"""Fit the network area to specified width, specified in node units.  This affects the zoom factor.

* width - The width to fit to."""
		pass
	def fitHeight(self, height) -> None: 
		"""Fit the network area to specified height, specified in node units. This affects the zoom factor.

* height - The height to fit to."""
		pass
	def home(self, zoom=True, op=None) -> None: 
		"""Home all operators in the network.

* zoom - (Keyword, Optional) When true, the view will be scaled accordingly, otherwise the nodes will only be re-centered.

* op - (Keyword, Optional) If an operator is specified, the network will be homed around its location.

```python


p = ui.panes['pane1']

n = op('/project1')

p.home(op=n)

p = ui.panes[2]

p.home(zoom=True)


```"""
		pass
	def homeSelected(self, zoom=True) -> None: 
		"""Home all selected operators in the network.

* zoom - (Keyword, Optional) When true, the view will be scaled accordingly, otherwise the nodes will only be re-centered."""
		pass
	def placeOPs(self, listOfOPs, inputIndex=None, outputIndex=None, delOP=None, undoName='Operators') -> None: 
		"""Use the mouse to place the specified operators in the pane.

* listOfOps - The list of operators to be placed.

* inputIndex - If specified, which input index to connect to.

* outputIndex - If specified, which output index to connect to.

* delOP - If specified, deletes that operator immediately after placing the listOfOPs.

* undoName - Describes the [[Undo]] operation."""
		pass
	pass


class noiseSOP(SOP,OP):
	""""""
	par : parameter.noiseSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.noiseSOP & parameter.SOP & parameter.OP"""
	pass


class noiseTOP(TOP,OP):
	""""""
	par : parameter.noiseTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.noiseTOP & parameter.TOP & parameter.OP"""
	pass


class normalmapTOP(TOP,OP):
	""""""
	par : parameter.normalmapTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.normalmapTOP & parameter.TOP & parameter.OP"""
	pass


class nullSOP(SOP,OP):
	""""""
	par : parameter.nullSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.nullSOP & parameter.SOP & parameter.OP"""
	pass


class nullTOP(TOP,OP):
	""""""
	par : parameter.nullTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.nullTOP & parameter.TOP & parameter.OP"""
	pass


class objectmergeSOP(SOP,OP):
	""""""
	par : parameter.objectmergeSOP|parameter.SOP|parameter.OP
	"""Parameters of parameter.objectmergeSOP & parameter.SOP & parameter.OP"""
	pass


class oculusriftTOP(TOP,OP):
	""""""
	par : parameter.oculusriftTOP|parameter.TOP|parameter.OP
	"""Parameters of parameter.oculusriftTOP & parameter.TOP & parameter.OP"""
	pass


class Poly(Prim):
	"""A Poly describes an instance of a single [[Polygon|geometry polygon]]. It is an instance of a [[Prim Class]]."""
	closed : bool
	"""Returns True if the poly is closed, False otherwise."""
	par : parameter.Poly|parameter.Prim
	"""Parameters of parameter.Poly & parameter.Prim"""
	pass



from ExtOpenVSCode import *
from custom_typings.QuickExt.NoNode import *
from custom_typings.QuickExt.CustomParHelper import *