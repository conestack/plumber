from zope.deprecation import deprecated
from plumber._behavior import Behavior
from plumber._plumber import plumber
from plumber._instructions import default
from plumber._instructions import override
from plumber._instructions import finalize
from plumber._instructions import plumb
from plumber._instructions import plumbifexists

Part = Behavior # B/C
deprecated('Part', """
``plumber.Part`` is deprecated as of plumber 1.2 and will be removed in
plumber 1.3. Use ``plumber.Behavior`` instead.""")

extend = override # B/C
deprecated('extend', """
``plumber.extend`` is deprecated as of plumber 1.2 and will be removed in 
plumber 1.3. Use ``plumber.override`` instead.""")
