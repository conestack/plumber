from __future__ import absolute_import
from plumber.behavior import Instructions
import abc


class Stacks(object):
    """organize stacks for parsing behaviors, stored in the class' dict."""

    attrname = '__plumbing_stacks__'

    def __init__(self, dct):
        self.dct = dct
        self.dct.setdefault(self.attrname, dict())
        self.stacks.setdefault('stages', dict())
        self.stages.setdefault('stage1', dict())
        self.stages.setdefault('stage2', dict())
        self.stacks.setdefault('history', [])

    stacks = property(lambda self: self.dct[self.attrname])
    stages = property(lambda self: self.stacks['stages'])
    stage1 = property(lambda self: self.stages['stage1'])
    stage2 = property(lambda self: self.stages['stage2'])
    history = property(lambda self: self.stacks['history'])


def searchnameinbases(name, bases):
    """Search name in base classes.

    .. code-block:: pycon

        >>> class A(object):
        ...     foo = 1

        >>> class B(A):
        ...     pass

        >>> searchnameinbases('foo', (B,))
        True
        >>> searchnameinbases('bar', (B,))
        False
    """
    for base in bases:
        if name in base.__dict__:
            return True
        if searchnameinbases(name, base.__bases__):
            return True
    return False


class Bases(object):
    """Used to search in base classes for attributes."""

    def __init__(self, bases):
        self.bases = bases

    def __contains__(self, name):
        return searchnameinbases(name, self.bases)


class plumber(type):
    """Metaclass for plumbing creation.

    Create and call a real plumber, for classes declaring a ``__plumbing__``
    attribute (inheritance is not enough):
    """
    __metaclass_hooks__ = list()

    @classmethod
    def metaclasshook(cls, func):
        cls.__metaclass_hooks__.append(func)
        return func

    def __new__(cls, name, bases, dct):
        if '__plumbing__' not in dct:
            return super(plumber, cls).__new__(cls, name, bases, dct)

        # turn single behavior into a tuple of one behavior
        plb = dct['__plumbing__']
        if type(plb) is not tuple:
            plb = dct['__plumbing__'] = (plb,)

        # stacks for parsing instructions
        stacks = Stacks(dct)

        # parse the behaviors
        for behavior in plb:
            for instruction in Instructions(behavior):
                stage = stacks.stages[instruction.__stage__]
                stack = stage.setdefault(instruction.__name__, [])
                stacks.history.append(instruction)
                if instruction not in stacks.history[:-1]:
                    if stack:
                        # XXX: check if case ever happens, otherwise remove
                        # if instruction.__stage__ > stack[-1].__stage__:
                        #     import warnings
                        #     msg = (
                        #         'Stage 1 instruction {} left of stage 2 '
                        #         'instruction {}. We consider deprecation of '
                        #         'this.'
                        #     ).format(stack[-1], instruction)
                        #     warnings.warn(msg, PendingDeprecationWarning)
                        instruction = stack[-1] + instruction
                    stack.append(instruction)
                    continue
                # already seen instruction is dropped

        # install stage1 instructions
        cls._install_stage1_instructions(bases, dct, stacks)

        # build the class and return it
        return super(plumber, cls).__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        super(plumber, cls).__init__(name, bases, dct)

        # install stage2 instructions
        if '__plumbing__' in dct:
            type(cls)._install_stage2_instructions(cls, dct, Stacks(dct))

        # run metaclass hooks
        for hook in plumber.__metaclass_hooks__:
            hook(cls, name, bases, dct)

    @staticmethod
    def _install_stage1_instructions(bases, dct, stacks):
        for stack in stacks.stage1.values():
            instruction = stack[-1]
            instruction(dct, Bases(bases))

    @staticmethod
    def _install_stage2_instructions(cls, dct, stacks):
        for stack in stacks.stage2.values():
            instruction = stack[-1]
            instruction(cls)


class abcplumber(abc.ABCMeta, plumber):
    """Metaclass for plumbing creation on abstract base class deriving objects.
    """

    def __new__(cls, name, bases, dct):
        return super(abcplumber, cls).__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        super(abcplumber, cls).__init__(name, bases, dct)

    @staticmethod
    def _install_stage1_instructions(bases, dct, stacks):
        for name, stack in stacks.stage1.items():
            abm = dct.get('__abstractmethods__', set())
            if name in abm:
                abm = set(abm)
                abm.remove(name)
                dct['__abstractmethods__'] = frozenset(abm)
                del dct[name]
            instruction = stack[-1]
            instruction(dct, Bases(bases))

    @staticmethod
    def _install_stage2_instructions(cls, dct, stacks):
        for name, stack in stacks.stage2.items():
            if name in dct.get('__abstractmethods__', set()):
                raise TypeError(
                    'Cannot plumb abstract method {}.{}'.format(
                        cls.__name__,
                        name
                    )
                )
            instruction = stack[-1]
            instruction(cls)


class plumbing(object):
    """Plumbing decorator."""

    def __init__(self, *behaviors):
        assert len(behaviors) > 0
        self.behaviors = behaviors

    def __call__(self, cls):
        # Basically taken from six
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars['__plumbing__'] = self.behaviors
        if type(cls) is abc.ABCMeta:
            type_ = abcplumber
        else:
            type_ = plumber
        return type_(cls.__name__, cls.__bases__, orig_vars)
