from plumber._behavior import Instructions
from plumber._behavior import behaviormetaclass


class Stacks(object):
    """organize stacks for parsing behaviors, stored in the class' dict
    """
    attrname = "__plumbing_stacks__"

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
    """
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
    """Used to search in base classes for attributes
    """
    def __init__(self, bases):
        self.bases = bases

    def __contains__(self, name):
        return searchnameinbases(name, self.bases)


class plumber(type):
    """Metaclass for plumbing creation

    Create and call a real plumber, for classes declaring a ``__plumbing__``
    attribute (inheritance is not enough):
    """
    def __new__(meta, name, bases, dct):
        if not dct.has_key('__plumbing__'):
            return type.__new__(meta, name, bases, dct)

        # turn single behavior into a tuple of one behavior
        if type(dct['__plumbing__']) is not tuple:
            dct['__plumbing__'] = (dct['__plumbing__'],)

        # stacks for parsing instructions
        stacks = Stacks(dct)

        # parse the behaviors
        for behavior in dct['__plumbing__']:
            for instruction in Instructions(behavior):
                stage = stacks.stages[instruction.__stage__]
                stack = stage.setdefault(instruction.__name__, [])
                stacks.history.append(instruction)
                if instruction not in stacks.history[:-1]:
                    if stack:
                        # XXX: replace by a non exception log warning
                        #if instruction.__stage__ > stack[-1].__stage__:
                        #    msg = 'Stage1 instruction %s left of stage2 '
                        #    'instruction %s. We consider deprecation of this.' \
                        #            % (stack[-1], instruction)
                        #    raise PendingDeprecationWarning(msg)
                        instruction = stack[-1] + instruction
                    stack.append(instruction)
                #else:
                    # XXX: replace by a non exception log warning
                    #raise Warning("Dropped already seen instruction %s." % \
                    #        (instruction,))

        # install stage1
        for stack in stacks.stage1.values():
            instruction = stack[-1]
            instruction(dct, Bases(bases))

        # build the class and return it
        return type.__new__(meta, name, bases, dct)

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)

        if dct.has_key('__plumbing__'):
            # install stage2
            stacks = Stacks(dct)
            for stack in stacks.stage2.values():
                instruction = stack[-1]
                instruction(cls)
