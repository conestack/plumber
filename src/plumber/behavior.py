from .instructions import Instruction
from .instructions import plumb
import warnings


try:
    from .instructions import _implements

    ZOPE_INTERFACE_AVAILABLE = True
except ImportError:  # pragma: no cover
    ZOPE_INTERFACE_AVAILABLE = False


class Instructions:
    """Adapter to set instructions on a behavior."""

    attrname = '__plumbing_instructions__'

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
    """Deprecated, ``Behavior`` collects instructions in ``__init_subclass__``."""

    def __init__(cls, name, bases, dct):
        warnings.warn(
            '``behaviormetaclass`` is deprecated, subclass ``Behavior`` instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(name, bases, dct)


class Behavior:
    """Base class for plumbing behaviors.

    Turns ``__doc__`` and implemented zope interfaces of subclasses into
    instructions and tells existing instructions their name and parent.
    ``Behavior`` itself is no behavior, its docstring is not plumbed.
    """

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        instructions = Instructions(cls)

        # An existing docstring is an implicit plumb instruction for __doc__
        if cls.__doc__ is not None:
            instructions.append(plumb(cls.__doc__, name='__doc__'))

        # If zope.interface is available treat existence of implemented
        # interfaces as an implicit _implements instruction with these
        # interfaces.
        if ZOPE_INTERFACE_AVAILABLE:
            instructions.append(_implements(cls))

        for name, item in cls.__dict__.items():
            # adopt instructions and enlist them
            if isinstance(item, Instruction):
                item.__name__ = name
                item.__parent__ = cls
                instructions.append(item)

        # XXX: introduce C3 resolution
        # check our bases for instructions we don't have already and which
        # are not overwritten by our instructions (stage1)
        for base in cls.__bases__:
            for instr in base.__dict__.get(Instructions.attrname, ()):
                # skip instructions we have already
                if instr in instructions:
                    continue
                # stage1 instructions with the same name are ignored
                if instr.__name__ in [
                    x.__name__ for x in instructions if x.__stage__ == 'stage1'
                ]:
                    continue
                instructions.append(instr)
