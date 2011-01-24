"""Instructions to be used in a plumbing part's declaration
"""
import os
import re
import types

# We are aware of ``zope.interface``: if zope.interfaces is available we check
# interfaces implemented on the plumbing parts and will make the plumbing
# implement them, too.
try:
    from zope.interface import classImplements
    from zope.interface import implementedBy
    ZOPE_INTERFACE_AVAILABLE = True
except ImportError:
    ZOPE_INTERFACE_AVAILABLE = False

from plumber.exceptions import PlumbingCollision


def plumb_doc(leftdoc, rightdoc):
    if leftdoc is None:
        return rightdoc
    if rightdoc is None:
        return leftdoc
    _next = re.search("^\s*.. plb_next::\s*$", leftdoc)
    if _next:
        return os.linesep.join((
            leftdoc[:_next.start()],
            rightdoc,
            leftdoc[_next.stop():]
            ))
    return os.linesep.join((leftdoc, rightdoc))


def payload(item):
    if not isinstance(item, Instruction):
        return item
    return payload(item.item)


class Instruction(object):
    """Base class for all plumbing instructions

    An instruction works on the attribute sharing its name, parent is the part
    declaring it. An instruction declares the stage to be applied in.
    """
    __name__ = None
    __parent__ = None
    __stage__ = None

    def __init__(self, item, name=None):
        self.item = item
        if name is not None:
            self.__name__ = name

    def __add__(self, right):
        """Used to merge current and previous instruction.

        Depending on the specific instruction the result is:
        - the previous instruction,
        - the current instruction or
        - a new instruction created from previous and current instruction
        """
        raise NotImplementedError

    def __call__(self, plumbing):
        """Apply instruction to a plumbing
        """
        raise NotImplementedError

    @property
    def name(self):
        return self.__name__

    @property
    def part(self):
        return self.__parent__

    @property
    def payload(self):
        return payload(self)

    def __repr__(self):
        return "<%(cls)s '%(name)s' of %(parent)s payload=%(payload)s>" % dict(
                cls=self.__class__.__name__,
                name=self.name or 'None',
                parent=self.__parent__ or 'None',
                payload=str(self.payload))

    __str__ = __repr__


class Stage1Instruction(Instruction):
    """Instructions installed in stage1
    """
    __stage__ = 'stage1'


class _docstring(Stage1Instruction):
    """Plumb __doc__
    """
    __name__ = "__doc__"

    def __add__(self, right):
        if not isinstance(right, _docstring):
            raise PlumbingCollision("Plumbing collision: %s + %s." % \
                    (self, right))
        return _docstring(plumb_doc(self.payload, right.payload))

    def __call__(self, plumbing):
        plumbing.__doc__ = plumb_doc(plumbing.__doc__, self.payload)


class _implements(Stage1Instruction):
    """classImplements interfaces
    """
    __name__ = "__interfaces__"

    def __add__(self, right):
        if not isinstance(right, _implements):
            raise PlumbingCollision(self, right)
        try:
            ifaces = self.payload + right.payload
        except TypeError:
            raise
        return _implements(ifaces)

    def __call__(self, plumbing):
        if self.payload:
            classImplements(plumbing, *self.payload)

    @property
    def payload(self):
        if type(self.item) is tuple:
            return self.item
        return tuple([x for x in implementedBy(self.item)])


class default(Stage1Instruction):
    """A default attribute
    """
    def __add__(self, right):
        """Everything except None wins against us
        """
        if isinstance(right, default):
            return self
        return right

    def __call__(self, plumbing):
        """declaration on the class or a base class wins against us.
        """
        if not hasattr(plumbing, self.name):
            setattr(plumbing, self.name, self.payload)


class extend(Stage1Instruction):
    """Extend the class
    """
    def __add__(self, right):
        """Overrule ``default``, collide with everything else
        """
        if isinstance(right, default):
            return self
        raise PlumbingCollision(self, right)

    def __call__(self, plumbing):
        """declaration on class collides with us, we win against base classes
        """
        if plumbing.__dict__.has_key(self.name):
            raise PlumbingCollision(plumbing, self)
        setattr(plumbing, self.name, self.payload)


class Stage2Instruction(Instruction):
    """Instructions installed in stage2
    """
    __stage__ = 'stage2'


def plumb(item):
    """Return instruction depending on what is to be plumbed 

    - _plumbcallable for a function
    - _plumbproperty for a property
    """
    if type(payload(item)) is property:
        return _plumbproperty(item)
    elif callable(payload(item)):
        return _plumbcallable(item)
    else:
        raise TypeError("%s cannot be plumbed" % (payload(item),))


def entrancefor(plumbing_method, _next):
    """An entrance for a plumbing method

    The entrance returned is a closure with signature: (self, *args, **kw), it
    wraps a call of plumbing_method curried with _next.
    """
    def entrance(self, *args, **kw):
        return plumbing_method(_next, self, *args, **kw)
    entrance.__doc__ = plumb_doc(plumbing_method.__doc__, _next.__doc__)
    entrance.__name__ = plumbing_method.__name__
    return entrance


def plumbingfor(plumbing_method, _next):
    def plumbing(__next, self, *args, **kw):
        return plumbing_method(
                    entrancefor(_next, __next),
                    self, *args, **kw
                    )
    plumbing.__doc__ = plumb_doc(plumbing_method.__doc__, _next.__doc__)
    plumbing.__name__ = plumbing_method.__name__
    return plumbing


class _plumbcallable(Stage2Instruction):
    """
    The signature of the method is:
    ``def foo(prt, _next, self, *args, **kw)``

    XXX:
    A plumbing method is a classmethod bound to the part class defining it
    (``prt``), as second argument it receives the next plumbing method
    (``_next``) and the third argument (``self``) is a plumbing instance, that
    for normal methods would be the first argument.

    In order to plumb a method there needs to be a non-plumbing method behind
    it provided by: a plumbing part via ``extend`` or ``default`` later in
    the pipeline, the class itself or one of its base classes.
    XXX
    """
    def __add__(self, right):
        return _plumbcallable(
                plumbingfor(self.plumbing_method, right.plumbing_method),
                name=self.name,
                )

    @property
    def plumbing_method(self):
        # If we have a parent, we return a method bound to it, our payload has
        # signature: def foo(prt, _next, self, *args, **kw)
        if self.part:
            return classmethod(self.payload).__get__(self.part)

        # We have no parent, don't belong to a part, are dynamically created,
        # our payload's sig: def foo(_next, self, *args, **kw)
        return self.payload

    def __call__(self, plumbing):
        # import here because of import loop, we could also move _Part to extra
        # module and use that
        import plumber

        # Check for a method on the plumbing class itself.
        try:
            _next = getattr(plumbing, self.name)
        except AttributeError:
            if not issubclass(plumbing, plumber.Part):
                raise
            _next = None

        plumbing_method = self.plumbing_method

        if issubclass(plumbing, plumber.Part):
            if _next is not None:
                plumbing_method = plumbingfor(plumbing_method, _next)
            setattr(plumbing, self.name, _plumbcallable(plumbing_method))
        else:
            # we need a method to plumb to
            if not callable(_next):
                raise TypeError("Cannot plumb %s to %s." % (self.item,
                    type(_next)))
            entrance = entrancefor(plumbing_method, _next)
            setattr(plumbing, self.name, entrance)


class _plumbproperty(Stage2Instruction):
    """mark a property as a plumbing property

    XXX:
    Signature of getter, setter and deleter:
    - ``def getter(plb, _next, self)``
    - ``def setter(plb, _next, self, val)``
    - ``def deleter(plb, _next, self)``

    In order to use a plumbing property, there needs to be a non-plumbing
    property on the class, by the time the end-points for getter, setter and
    deleter are looked up, provided by a plumbing ``extend`` or ``default``,
    the plumbing class itself, or one of its base classes.
    XXX
    """
    def __call__(self, plumbing):
        _nextprop = getattr(plumbing, self.name)

        if not type(_nextprop) is property:
            raise TypeError("Cannot plumb %s to %s." % (self.item, _nextprop))
        
        # merge property doc
        edoc = merge_doc(_nextprop, self.item)

        # create entrance getter/setter/deleter
         

        # create normal property serving as entrance to the chained
        # getters/setters/deleters with accumulated doc.
        entranceprop = property(eget, eset, edel, edoc)

        # put entrance property into plumbing class' ``__dict__``
        setattr(plumbing, self.name, entranceprop)
        self.pipe(plumbing).append(self)
