from plumber._part import Instructions
from plumber._part import PartMetaclass


class Stacks(object):
    """organize stacks for parsing parts
    """
    attrname = "__plumbing_stacks__"

    def __init__(self, plumbing):
        self.plumbing = plumbing
        if not self.attrname in self.plumbing.__dict__:
            setattr(self.plumbing, self.attrname, dict())
        self.stacks.setdefault('stages', dict())
        self.stages.setdefault('stage1', dict())
        self.stages.setdefault('stage2', dict())
        self.stacks.setdefault('history', [])

    stacks = property(lambda self: getattr(self.plumbing, self.attrname))
    stages = property(lambda self: self.stacks['stages'])
    stage1 = property(lambda self: self.stages['stage1'])
    stage2 = property(lambda self: self.stages['stage2'])
    history = property(lambda self: self.stacks['history'])


class RealPlumber(Stacks):
    """Does the plumbing work

    A plumber is an instance object bound to a plumbing class during
    initialization. On call it parses the class' pipeline declaration and
    installs the result on the class.
    """
    def __init__(self, plumbing):
        """Initialize stacks, turn pipeline into tuple and remember plumbing
        """
        super(RealPlumber, self).__init__(plumbing)
        if type(plumbing.__plumbing__) is not tuple:
            plumbing.__plumbing__ = (plumbing.__plumbing__,)
        self.plumbing = plumbing

    def __call__(self):
        """Parse the parts into stacks and install the result afterwards
        """
        # parse the parts, nested tuples are flatened
        for part in self.plumbing.__plumbing__:
            for instruction in Instructions(part):
                self.merge(instruction)

        # Install stages
        for name, stage in sorted(self.stages.iteritems()):
            self.install(stage)

    def install(self, stage):
        """Apply latest instruction from each stack of the stage
        """
        for stack in stage.values():
            instruction = stack[-1]
            instruction(self.plumbing)

    def merge(self, instruction):
        """merge instruction with latest instruction and append result to stack
        """
        stage = self.stages[instruction.__stage__]
        stack = stage.setdefault(instruction.__name__, [])
        if stack:
            instruction = stack[-1] + instruction
        stack.append(instruction)
        self.history.append(instruction)


class Plumber(PartMetaclass):
    """Metaclass for plumbing creation

    Create and call a real plumber, for classes declaring a ``__plumbing__``
    attribute (inheritance is not enough):
    """
    def __init__(cls, name, bases, dct):
        super(Plumber, cls).__init__(name, bases, dct)
        if cls.__dict__.has_key('__plumbing__'):
            real_plumber = RealPlumber(cls)
            real_plumber()
