class plumbing(classmethod):
    """Decorator that makes a function part of the plumbing

    A plumbing method is a classmethod bound to the class defining it. As
    second argument it expects the next plumbing method, typically called
    _next. The third argument is the object that for normal methods would be
    the first argument, typically named self.

    XXX: rename to plumbingmethod?
    """


def plumb(plumbing_method, next_method):
    """plumbs two methods together

    The first method is expected to be a plumbing method, i.e. a method defined
    in a class with the plumbing decorator. ``next_method`` can be an arbitrary
    function, though typically it will at least accept one argument (self).
    """
    def plumbed_method(self, *args, **kws):
        """A normal method, plumbed to the next normal method
        """
        return plumbing_method(next_method, self, *args, **kws)

    return plumbed_method


def entrance(name, pipe):
    """Create an entrance to the plumbing
    """
    # The last method may not be a plumbing method, as there is nothing to pass
    # to it as _next.
    #
    # XXX: We may support automatic creation of that exit method, but like this
    # it is explicit and it feels better this way.
    exit_method = pipe.pop()
    plumbed_methods = [exit_method]

    # In case there was only one method, no plumbing needs to be done.
    # Otherwise, we take the next method from the end of the pipe and plumb it
    # in front of the previously plumbed methods.
    while pipe: 
        plumbed_methods.insert(0, plumb(pipe.pop(), plumbed_methods[0]))

    return plumbed_methods[0]


class Plumber(type):
    """Metaclass to create classes using pipelines

    Expects a __pipeline__ attribute on the class it is working on. The last
    element of the pipeline needs to be something normal, without plumbing
    methods.

    XXX: Introduce base class ?
    
    XXX: introduce Inherited pipeline plugin?

    XXX: introduce Self pipeline plugin?

    XXX: call to super as exit node would also be easy
    """
    def __init__(cls, name, bases, dct):
        super(Plumber, cls).__init__(name, bases, dct)
        # Gather all functions that are part of the plumbing and line up the
        # pipelines for the individual methods
        pipelines = {}
        for plugin in cls.__pipeline__:
            for name, func in plugin.__dict__.items():
                if not isinstance(func, plumbing):
                    continue
                pipe = pipelines.setdefault(name, [])
                pipe.append(getattr(plugin, name))

        # For all pipelines started by plumbing methods we need normal methods
        # as exit points. These are provided by the last plugin.
        for name in pipelines:
            pipelines[name].append(getattr(plugin, name))
        for name, pipe in pipelines.items():
            # XXX: methods defined in the class are just killed
            setattr(cls, name, entrance(name, pipe))
