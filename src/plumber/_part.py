from plumber.exceptions import PlumbingCollision
from plumber._instructions import Instruction
from plumber._instructions import plumb

try:
    from plumber._instructions import _implements
    ZOPE_INTERFACE_AVAILABLE = True
except ImportError: #pragma NO COVERAGE
    # zope.testrunner depends on zope.interface
    # XXX: how do we test without zope.interface?
    ZOPE_INTERFACE_AVAILABLE = False #pragma NO COVERAGE
    

class _Part(object):
    """Just here to solve a dependency loop
    """


class Instructions(object):
    """Adapter to set instructions on a part
    """
    attrname = "__plumbing_instructions__"

    def __init__(self, part):
        self.part = part
        if not part.__dict__.has_key(self.attrname):
            setattr(part, self.attrname, [])

    def __iter__(self):
        return iter(self.instructions)

    @property
    def instructions(self):
        return getattr(self.part, self.attrname)


class partmetaclass(type):
    """Metaclass for part creation

    Turn __doc__ and implemented zope interfaces into instructions and tell
    existing instructions their name and parent, for subclasses of ``Part``.
    """
    def __init__(cls, name, bases, dct):
        super(partmetaclass, cls).__init__(name, bases, dct)
        if not issubclass(cls, _Part):
            return

        # Get the part's instructions list
        instructions = Instructions(cls).instructions

        # An existing docstring is an implicit plumb instruction for __doc__
        if cls.__doc__ is not None:
            instructions.append(plumb(cls.__doc__, name='__doc__'))

        # If zope.interface is available treat existence of implemented
        # interfaces as an implicit _implements instruction with these
        # interfaces.
        if ZOPE_INTERFACE_AVAILABLE:
            instructions.append(_implements(cls))

        for name, item in cls.__dict__.iteritems():
            # adopt instructions and enlist them
            if isinstance(item, Instruction):
                item.__name__ = name
                item.__parent__ = cls
                instructions.append(item)
        for base in bases:
            for instruction in Instructions(base):
                # skip instructions from bases for attributes we already have
                # an instruction for - this reflects normal subclassing
                # behaviour.
                if not instruction.__name__ in cls.__dict__:
                    instructions.append(instruction)


# Base class for plumbing parts: identification and metaclass setting
# No doctest allowed here, it would be recognized as an instruction.
class Part(_Part):
    __metaclass__ = partmetaclass
