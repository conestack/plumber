import os

# We are aware of ``zope.interface.Interface``: if zope.interfaces is available
# we check interfaces implemented on the plumbing plugins and will make the
# plumbing implement them, too.
try:
    from zope.interface import classImplements
    from zope.interface import implementedBy
    ZOPE_INTERFACE_AVAILABLE = True
except ImportError:
    ZOPE_INTERFACE_AVAILABLE = False


class PlumbingCollision(RuntimeError):
    pass


class default(object):
    """Provide a default value for something

    The first plugin with a default value wins the first round: its value is
    set on the plumbing as if it was declared there.

    Attributes set with the ``extend`` decorator overrule ``default``
    attributes (see ``extend`` decorator).
    """
    def __init__(self, attr):
        self.attr = attr


class extend(object):
    """Declare an attribute on the plumning as if it was defined on it.

    Attribute set with the ``extend`` decorator overrule ``default``
    attributes. Two ``extend`` attributes in a chain raise a PlumbingCollision.
    """
    def __init__(self, attr):
        self.attr = attr


class plumb(classmethod):
    """Mark a method to be used in a plumbing chain.

    The signature of the method is:
    ``def foo(plb, _next, self, *args, **kws)``

    A plumbing method is a classmethod bound to the plugin class defining it
    (``plb``), as second argument it receives the next plumbing method
    (``_next``) and the third argument (``self``) is a plumbing instance, that
    for normal methods would be the first argument.

    In order to plumb a method there needs to be a non-plumbing method behind
    it provided by: a plumbing plugin via ``extend`` or ``default`` later in
    the pipeline, the class itself or one of its base classes.
    """

def merge_doc(first, *args):
    if first.__doc__ is None:
        return None
    if not args:
        return first.__doc__
    return os.linesep.join((first.__doc__, merge_doc(*args)))


def entrance(name, pipe):
    """Create an entrance to a pipeline.

    recursively:
    - pop first method from pipeline
    - create entrance to the rest of the pipe as _next
    - wrap method passing it _next and return it, if not last method
    - return last method as is, if last method
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
    _entrance.__doc__ = merge_doc(_next, plumbing_method)
    return _entrance


class CLOSED(object):
    """used for marking a pipeline as closed
    """


class Plumber(type):
    """Metaclass for plumbing creation

    First the normal new-style metaclass ``type()`` is called to construct the
    class with ``name``, ``bases``, ``dct``.

    Then, if the class declares a ``__pipeline__`` attribute, the plumber
    will create a plumbing system accordingly. Attributes declared with
    ``default``, ``extend`` and ``plumb`` will be used in the plumbing.
    """
    def __init__(cls, name, bases, dct):
        super(Plumber, cls).__init__(name, bases, dct)
        # The metaclass is inherited.
        # The plumber will only get active if the class it produces defines a
        # __pipeline__.
        if cls.__dict__.get('__pipeline__') is None:
            return

        # generate docstrings from all plugin classes
        cls.__doc__ = merge_doc(cls, *reversed(cls.__pipeline__))

        # Follow ``default``, ``extend`` and ``plumb`` declarations.
        pipelines = {}
        defaulted = {}
        for plugin in cls.__pipeline__:

            for name, decor in plugin.__dict__.items():
                if isinstance(decor, extend):
                    if name in cls.__dict__ \
                      and name not in defaulted:
                        # XXX: provide more info what is colliding
                        raise PlumbingCollision(name)
                    # just copy the attribute that was passed to the extend
                    # decorator and mark the pipeline as closed, i.e. adding
                    # further methods to it, will raise an error.
                    setattr(cls, name, decor.attr)
                    defaulted.pop(name, None)
                    pipe = pipelines.setdefault(name, [])
                    pipe.append(CLOSED)
                elif isinstance(decor, default):
                    if not name in cls.__dict__:
                        setattr(cls, name, decor.attr)
                        defaulted[name] = None
                elif isinstance(decor, plumb):
                    pipe = pipelines.setdefault(name, [])
                    if pipe and pipe[-1] is CLOSED:
                        raise PlumbingCollision(name)
                    if name in defaulted:
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
            # Remove CLOSED pipe marker.
            if pipe[-1] is CLOSED:
                del pipe[-1]

            # Retrieve end point from class, from what happened above it is
            # found with priorities:
            # 1. a plumbing plugin declared it with ``extend``
            # 2. the plumbing class itself declared it
            # 3. a plumbing plugin provided a ``default`` value
            # 4. a base class provides the attribute
            end_point = getattr(cls, name)
            pipe.append(end_point)

            # Finally ``entrance`` will plumb the methods together and return
            # an entrance function, that is set on the plumbing class be and
            # will result in a normal bound method when being retrieved by
            # getattr().
            setattr(cls, name, entrance(name, pipe))
