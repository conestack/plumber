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


class Bases(object):
    """Singleton used as last pipeline element to indicate that normal mro is
    used to find exit points
    """


class Plumber(type):
    """Metaclass to create classes using a plumbing

    First the Plumber will read the __pipeline__ attribute of the new class and
    create a plumbing class accordingly based on the bases passed for the new
    class. The new class will then have the plumbing class as its single base.

    This results in the new class being a subclass of the specified bases as
    well as the possibily to override new methods in the class and calling the
    plumbing class via super.


    XXX: introduce Inherited pipeline plugin?

    XXX: introduce Self pipeline plugin?

    XXX: call to super as exit node would also be easy
    """
    def __init__(cls, name, bases, dct):
        super(Plumber, cls).__init__(name, bases, dct)
        if cls.__dict__.get('__metaclass__') is None:
            return
        # Gather all functions that are part of the plumbing and line up the
        # pipelines for the individual methods. The last pipeline element is
        # special. In contrast to the other pipeline elements it may not
        # define plumbing methods, but only normal methods. It is ignored
        # during the gathering and only methods that have corresponding
        # plumbing methods will be used as exit points for these.
        pipelines = {}
        for plugin in cls.__pipeline__[:-1]:
            for name, func in plugin.__dict__.items():
                if not isinstance(func, plumbing):
                    continue
                pipe = pipelines.setdefault(name, [])
                pipe.append(getattr(plugin, name))

        # Check the last pipeline element. If it is Bases, we will create a
        # temporary class based on the same bases as the new class in order to
        # use the mro mechanism to give us the exit points. Finally we create
        # an entrance method to the plumbing and set it on the new class.
        if cls.__pipeline__[-1] is Bases:
            final_element = type('Tmp', bases, {})
        else:
            final_element = cls.__pipeline__[-1]
        for name, pipe in pipelines.items():
            # XXX: probably we should catch AttributeErrors
            exit_method = getattr(final_element, name)
            pipe.append(exit_method)

            # XXX: methods defined in the class are just killed - at least add
            # a warning.
            setattr(cls, name, entrance(name, pipe))
