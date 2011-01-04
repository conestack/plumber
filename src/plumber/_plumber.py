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
    """Create an entrance to the plumbing, and the whole pipeline behind it
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
        # The plumber will only get active if the class asks for explicitly. It
        # is not enough that a class inherits the __metaclass__ declaration
        # from one of its bases, but it needs to do so itself. This enables
        # subclassing a class that uses a plumber.
        if cls.__dict__.get('__metaclass__') is None:
            return

        # Gather all functions that are part of the plumbing and line up the
        # pipelines for the individual methods. Only methods that are decorated
        # with the plumning decorator are taken in.
        pipelines = {}
        for plugin in cls.__pipeline__:
            for name, func in plugin.__dict__.items():
                if not isinstance(func, plumbing):
                    continue
                pipe = pipelines.setdefault(name, [])
                pipe.append(getattr(plugin, name))

        for name, pipe in pipelines.items():
            # For each pipeline we will now ask the MRO to give us a method to
            # be used as an endpoint. An endpoint is therefore a normal method
            # and not a plumbing anymore. Apart from that, any plumbing method
            # can decide not to use its _next and just be the innermost method
            # being called. In case the MRO does not give us a method, i.e. we
            # get an AttributeError, we will provide a method that raises a
            # NotImplementedError. By that, it is possible for the class to be
            # built, but in order for a runtime call to succeed there needs to
            # be a plumbing method in front, which will not make use of its
            # _next method and therefore build the end point. So plumbing
            # methods can extend a class with new functionality and even make a
            # super call, just as if the method would be defined on the class.
            def notimplemented(*args, **kws):
                raise NotImplementedError
            end_point = getattr(cls, name, notimplemented)
            pipe.append(end_point)

            # Finally ``entrance`` will plumb the methods together and return
            # us an entrance method, that can be set on the class and will
            # result in a normal bound method when being retrieved by
            # getattr().
            entrance_method = entrance(name, pipe)

            # If there is a method with same name as a pipe, it is now part of
            # the the pipe as innermost method and will be overwritten on the
            # class. It lives on by being referenced in the pipeline as the
            # innermost method and end point of the pipeline. Via super it can
            # call the next method in the MRO, but anyway it is the end point
            # of the plumbing.
            setattr(cls, name, entrance_method)
