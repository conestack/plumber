from plumber.exceptions import PlumbingCollision
from plumber._instructions import Instruction
from plumber._instructions import _docstring
from plumber._instructions import _implements

# We are aware of ``zope.interface``: if zope.interfaces is available we check
# interfaces implemented on the plumbing parts and will make the plumbing
# implement them, too.
try:
    import zope.interface
    ZOPE_INTERFACE_AVAILABLE = True
except ImportError:
    ZOPE_INTERFACE_AVAILABLE = False


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


class PartMetaclass(type):
    """Metaclass for part creation

    Turn __doc__ and implemented zope interfaces into instructions and tell
    existing instructions their name and parent, for subclasses of ``Part``.
    """
    def __init__(cls, name, bases, dct):
        super(PartMetaclass, cls).__init__(name, bases, dct)
        if not issubclass(cls, _Part):
            return

        # Get the part's instructions list
        instructions = Instructions(cls).instructions

        # An existing docstring is an implicit _docstring instruction
        if cls.__doc__ is not None:
            instructions.append(_docstring(cls.__doc__))

        # If zope.interface is available treat existence of implemented
        # interfaces as an implicit _implements instruction with these
        # interfaces.
        if ZOPE_INTERFACE_AVAILABLE:
            instructions.append(_implements(cls))

        for name, item in cls.__dict__.iteritems():
            if isinstance(item, Instruction):
                item.__name__ = name
                item.__parent__ = cls
                instructions.append(item)
        for base in bases:
            instructions += Instructions(base).instructions


# Base class for plumbing parts: identification and metaclass setting
# No doctest allowed here, it would be recognized as an instruction.
class Part(_Part):
    __metaclass__ = PartMetaclass
