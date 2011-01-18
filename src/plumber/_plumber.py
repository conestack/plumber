import exceptions
import os
import types

# If zope.interfaces is available we are aware of interfaces implemented on
# plumbing classes and will make the factored class implement them, too.
try:
    from zope.interface import classImplements
    from zope.interface import implementedBy
    ZOPE_INTERFACE_AVAILABLE = True
except ImportError:
    ZOPE_INTERFACE_AVAILABLE = False


class PlumbingCollision(RuntimeError):
    pass


class plumberitem(classmethod):
    """An item the plumber will recognize and use
    """


class extend(object):
    """Instructs the plumber to just copy an item into the class' ``__dict__``.

    If an item with the same name already exists, a PlumbingCollision is raised.
    """
    def __init__(self, item):
        self.item = item


class plumb(plumberitem):
    """Instructs the plumber to plumb a method or property into the plumbing

    XXX

    A plumbing method is a classmethod bound to the plugin class defining it
    (``plb``), as second argument it expects the next plumbing method
    (``_next``) and the third argument (``self``) is the object that for normal
    methods would be the first argument.

    The signature of the function is:
    ``def foo(plb, _next, self, *args, **kws)``

    In order to plumb a method there needs to be a non-plumbing method behind
    it, provided by: a plumbing plugin via extend later in the pipeline, the
    class itself or one of its base classes.
    """


def entrance(name, pipe):
    """Plumbs all methods of a pipeline together and returns the entrance.

    recursively:
    - pop first method
    - create entrance to the rest of the pipe as _next
    - wrap method passing it _next, if not last method
    - return last method as is
    """
    # If only one element is left in the pipe, it is a normal method that does
    # not expect a ``_next`` parameter.
    if len(pipe) is 1:
        return pipe[0]

    # XXX: traceback supplement for pdb, probably more than just name is needed

    plumbing_method = pipe.pop(0)
    _next = entrance(name, pipe)
    def _entrance(self, *args, **kw):
        return plumbing_method(_next, self, *args, **kw)
    if _next.__doc__ is not None:
        _entrance.__doc__ = os.linesep.join((
                _next.__doc__,
                plumbing_method.__doc__ or ''
                ))
    return _entrance


class CLOSED(object):
    """used for marking a pipeline as closed
    """


class Plumber(type):
    """Metaclass to create classes using a plumbing

    First the normal new-style metaclass ``type()`` is called to construct the
    class with ``name``, ``bases``, ``dct``.

    Then, if the class declares a ``__pipeline__`` attribute, the plumber
    creates a plumbing system accordingly and puts it in front of the class.
    Methods defined on the class itself or inherited via base classes serve as
    end points for the plumbing system.
    """
    def __init__(cls, name, bases, dct):
        super(Plumber, cls).__init__(name, bases, dct)
        # The metaclass is inherited.
        # The plumber will only get active if the class it produces defines a
        # __pipeline__.
        if cls.__dict__.get('__pipeline__') is None:
            return

        # Gather all things decorated either with ``extend`` or ``plumb`` and
        # line up plumbing functions with the same name in pipelines.
        pipelines = {}
        for plugin in cls.__pipeline__:
            for name, item in plugin.__dict__.items():
                if not isinstance(item, (extend, plumb)):
                    continue
                pipe = pipelines.setdefault(name, [])
                if isinstance(item, extend):
                    if name in cls.__dict__:
                        # XXX: provide more info what is colliding
                        raise PlumbingCollision(name)
                    # just copy the item that was passed to the extend
                    # decorator and mark the pipeline as closed, i.e. adding
                    # further methods to it, will raise an error.
                    cls.__dict__[name] = item.item
                    pipe.append(CLOSED)
                elif isinstance(item, plumb):
                    if pipe and pipe[-1] is CLOSED:
                        raise PlumbingCollision(name)
                    # plumbing methods are class methods bound to the plumbing
                    # plugin class, ``getattr`` on the class in combination
                    # with being a classmethod, does this for us.
                    pipe.append(getattr(plugin, name))

            # If zope.interface is available (see import at the beginning of
            # file), we check the plugins for implemented interfaces and make
            # the new class implement these, too.
            if ZOPE_INTERFACE_AVAILABLE:
                ifaces = implementedBy(plugin)
                if ifaces is not None:
                    classImplements(cls, *list(ifaces))

        for name, pipe in pipelines.items():
            # XXX
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
            # XXX
            #def notimplemented(*args, **kws):
            #    raise NotImplementedError
            end_point = getattr(cls, name)
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
            # call the next method in the MRO, but anyway it is the default end
            # point of the plumbing.
            setattr(cls, name, entrance_method)
