from __future__ import absolute_import
from plumber.behavior import Instructions


class Stacks(object):
    """Organize stacks for parsing behaviors, stored in the class dict."""

    def __init__(self, dct):
        dct['__plumbing_stacks__'] = self
        self.history = list()
        self.stage1 = dict()
        self.stage2 = dict()


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

    @staticmethod
    def apply_metaclasshooks(cls, name, bases, dct):
        for hook in plumber.__metaclass_hooks__:
            hook(cls, name, bases, dct)
        return cls

    @staticmethod
    def derived_members(bases, attrs=None):
        if attrs is None:
            attrs = set()
        for base in bases:
            attrs.update(base.__dict__)
            plumber.derived_members(base.__bases__, attrs=attrs)
        return attrs

    @staticmethod
    def parse_behaviors(plb, dct):
        # Stacks for parsing instructions.
        stacks = Stacks(dct)
        history = stacks.history

        # Parse the behaviors.
        for behavior in plb:
            for instruction in Instructions(behavior):
                # already seen instruction are ignored
                if instruction not in history:
                    stage = getattr(stacks, instruction.__stage__)
                    instruction_name = instruction.__name__
                    prev_instruction = stage.get(instruction_name)
                    if prev_instruction:
                        instruction = prev_instruction + instruction
                    stage[instruction_name] = instruction
                history.append(instruction)
        return stacks

    def __new__(mcls, name, bases, dct):
        # No plumbing behaviors. Apply metaclasshooks and return class.
        if '__plumbing__' not in dct:
            cls = super(plumber, mcls).__new__(mcls, name, bases, dct)
            return plumber.apply_metaclasshooks(cls, name, bases, dct)

        # Ensure plumbing behaviors are iterable.
        plb = dct['__plumbing__']
        if type(plb) is not tuple:
            plb = dct['__plumbing__'] = (plb,)

        # Parse behaviors
        stacks = plumber.parse_behaviors(plb, dct)

        # Install stage 1.
        members = plumber.derived_members(bases)
        for instruction in stacks.stage1.values():
            instruction(dct, members)

        # Build the class.
        cls = super(plumber, mcls).__new__(mcls, name, bases, dct)

        # Install stage 2.
        for instruction in stacks.stage2.values():
            instruction(cls)

        # Apply metaclasshooks and return class.
        return plumber.apply_metaclasshooks(cls, name, bases, dct)


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
        return plumber(cls.__name__, cls.__bases__, orig_vars)
