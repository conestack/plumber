from zope.deprecation import deprecated
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


class _Behavior(object):
    """Just here to solve a dependency loop
    """


class Instructions(object):
    """Adapter to set instructions on a behavior
    """
    attrname = "__plumbing_instructions__"

    def __init__(self, behavior):
        self.behavior = behavior
        if not behavior.__dict__.has_key(self.attrname):
            setattr(behavior, self.attrname, [])

    def __contains__(self, item):
        return item in self.instructions

    def __iter__(self):
        return iter(self.instructions)

    def append(self, item):
        self.instructions.append(item)

    @property
    def instructions(self):
        return getattr(self.behavior, self.attrname)


class behaviormetaclass(type):
    """Metaclass for behavior creation

    Turn __doc__ and implemented zope interfaces into instructions and tell
    existing instructions their name and parent, for subclasses of ``Behavior``.

        >>> class A(object):
        ...     __metaclass__ = behaviormetaclass

        >>> getattr(A, '__plumbing_instructions__', 'No behavior')
        'No behavior'

        >>> class A(Behavior):
        ...     __metaclass__ = behaviormetaclass

        >>> getattr(A, '__plumbing_instructions__', None) and 'Behavior'
        'Behavior'

    """
    def __init__(cls, name, bases, dct):
        super(behaviormetaclass, cls).__init__(name, bases, dct)
        if not issubclass(cls, _Behavior):
            return

        # Get the behavior's instructions list
        instructions = Instructions(cls)

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

        # XXX: introduce C3 resolution
        # check our bases for instructions we don't have already and which
        # are not overwritten by our instructions (stage1)
        for base in bases:
            # XXX: I don't like this code
            for instr in Instructions(base):
                # skip instructions we have already
                if instr in instructions:
                    continue
                # stage1 instructions with the same name are ignored
                if instr.__name__ in [x.__name__ for x in instructions if
                        x.__stage__ == 'stage1']:
                    continue
                instructions.append(instr)


# Base class for plumbing behaviors: identification and metaclass setting
# No doctest allowed here, it would be recognized as an instruction.
class Behavior(_Behavior):
    __metaclass__ = behaviormetaclass


Part = Behavior # B/C
deprecated('Part',
           ('Part is deprecated as of plumber 1.2 and will be removed '
            'in plumber 1.3'))