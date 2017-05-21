from __future__ import absolute_import
from plumber.compat import add_metaclass
from plumber.instructions import Instruction
from plumber.instructions import plumb
import sys


try:
    from plumber.instructions import _implements
    ZOPE_INTERFACE_AVAILABLE = True
except ImportError:                                          # pragma: no cover
    ZOPE_INTERFACE_AVAILABLE = False


ITER_FUNC = 'iteritems' if sys.version_info[0] < 3 else 'items'


class _Behavior(object):
    """Just here to solve a dependency loop
    """


class Instructions(object):
    """Adapter to set instructions on a behavior
    """
    attrname = "__plumbing_instructions__"

    def __init__(self, behavior):
        self.behavior = behavior
        if self.attrname not in behavior.__dict__:
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
    existing instructions their name and parent, for subclasses of
    ``Behavior``.

        >>> from plumber.compat import add_metaclass

        >>> @add_metaclass(behaviormetaclass)
        ... class A(object):
        ...     pass

        >>> getattr(A, '__plumbing_instructions__', 'No behavior')
        'No behavior'

        >>> @add_metaclass(behaviormetaclass)
        ... class A(Behavior):
        ...     pass

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

        for name, item in getattr(cls.__dict__, ITER_FUNC)():
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
@add_metaclass(behaviormetaclass)
class Behavior(_Behavior):
    pass
