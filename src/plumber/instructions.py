from __future__ import absolute_import
from plumber.compat import STR_TYPE
from plumber.exceptions import PlumbingCollision
try:
    from zope.interface import classImplements
    from zope.interface import implementedBy
    ZOPE_INTERFACE_AVAILABLE = True
except ImportError:  # pragma: no cover
    ZOPE_INTERFACE_AVAILABLE = False
import re


###############################################################################
# Instruction base class and helper function
###############################################################################

def payload(item):
    """Get to the payload through a chain of instructions.

    .. code-block:: pycon

        >>> from plumber.instructions import Instruction
        >>> from plumber.instructions import payload

        >>> class Foo:
        ...     pass

        >>> payload(Instruction(Instruction(Foo))) is Foo
        True

    """
    if not isinstance(item, Instruction):
        return item
    return payload(item.item)


def plumb_str(leftdoc, rightdoc):
    """helper function to plumb two doc strings together.

    A ``__plbnext__`` tag is replaced with rightdoc, it needs to be preceeded
    and followed by an empty line.

    .. code-block:: pycon

        >>> from plumber.instructions import plumb_str

        >>> leftdoc = '''Left head
        ...
        ... __plbnext__
        ...
        ... Left tail
        ... '''

        >>> rightdoc = '''Right head
        ...
        ... __plbnext__
        ...
        ... Right tail
        ... '''

        >>> print(plumb_str(leftdoc, rightdoc))
        Left head
        <BLANKLINE>
        Right head
        <BLANKLINE>
        __plbnext__
        <BLANKLINE>
        Right tail
        <BLANKLINE>
        Left tail
        <BLANKLINE>

    Otherwise leftdoc is appended to rightdoc, separated by a newline, it is
    assumed there is a ``__plbnext__`` tag at the beginning of leftdoc.

    .. code-block:: pycon

        >>> leftdoc = '''Left tail
        ... '''

        >>> rightdoc = '''Right tail
        ... '''

        >>> print(plumb_str(leftdoc, rightdoc))
        Right tail
        <BLANKLINE>
        Left tail
        <BLANKLINE>

        >>> class A: pass
        >>> plumb_str(A, None) is A
        True

        >>> plumb_str(None, A) is A
        True

        >>> plumb_str(None, None) is None
        True

    """
    if leftdoc is None:
        return rightdoc
    if rightdoc is None:
        return leftdoc
    next_ = re.search(r'\n\s*\n\s*__plbnext__\s*\n\s*\n', leftdoc)
    if not next_:
        return '\n\n'.join((rightdoc.rstrip(), leftdoc))
    return leftdoc.replace('__plbnext__', rightdoc.rstrip())


class Instruction(object):
    """Base class for all plumbing instructions.

    An instruction works on the attribute sharing its name, parent is the part
    declaring it. An instruction declares the stage to be applied in.
    """
    __name__ = None
    __parent__ = None
    __stage__ = None

    def __init__(self, item, name=None):
        """Create instruction.

        .. code-block:: pycon

            >>> class Foo:
            ...     pass

            >>> Instruction(Foo).item is Foo
            True

            >>> Instruction(Foo).__name__ is None
            True

            >>> Instruction(Foo, name='foo').__name__ == 'foo'
            True

        """
        self.item = item
        if name is not None:
            self.__name__ = name

    def __add__(self, right):
        """Used to merge instructions, subclasses need to implement it.

        .. code-block:: pycon

            >>> Instruction(None) + 1
            Traceback (most recent call last):
              ...
            NotImplementedError

        """
        raise NotImplementedError

    def __call__(self, dct, derived_members=None):
        """Apply instruction to a plumbing, subclasses need to implement it.

        .. code-block:: pycon

            >>> Instruction(None)(None)
            Traceback (most recent call last):
              ...
            NotImplementedError

        ``derived_members`` is a set containing all base class members of the
        plumbing, instructions may or may not need it.
        """
        raise NotImplementedError

    def __eq__(self, right):
        """Instructions are equal if:

        - they are the very same
        - their class is the very same and their payloads are equal
        """
        # breaking up boolean expressions makes them more transparent for test
        # coverage
        if self is right:
            return True
        if self.__class__ is not right.__class__:
            return False
        if self.name == right.name:
            if self.payload == right.payload:
                return True
        return False

    @property
    def name(self):
        return self.__name__

    @property
    def payload(self):
        return payload(self)

    def __repr__(self):
        return "<%(cls)s '%(name)s' of %(parent)s payload=%(payload)s>" % dict(
            cls=self.__class__.__name__,
            name=self.name or 'None',
            parent=self.__parent__ or 'None',
            payload=repr(self.payload)
        )

    __str__ = __repr__


###############################################################################
# Stage 1 instructions
###############################################################################

class Stage1Instruction(Instruction):
    """Instructions installed in stage1.

    - default
    - override
    - finalize
    """
    __stage__ = 'stage1'


class default(Stage1Instruction):
    """Provide a default attribute.

    A default attribute is used, if neither the class nor one of its bases
    declare the attribute.

    For default/override/finalize merging see ``__add__`` here,
    ``override.__add__`` and ``finalize.__add__``.
    """

    def __add__(self, right):
        """First default wins from left to right.

        .. code-block:: pycon

            >>> from plumber.instructions import default

            >>> def1 = default(1)
            >>> def1 + def1 is def1
            True

            >>> def2 = default(2)
            >>> def1 + def2 is def1
            True

            >>> def2 + def1 is def2
            True

        Override wins over default.

        .. code-block:: pycon

            >>> from plumber.instructions import override

            >>> ext3 = override(3)
            >>> def1 + ext3 is ext3
            True

        Finalize wins over default.

        .. code-block:: pycon

            >>> from plumber.instructions import finalize

            >>> fin4 = finalize(4)
            >>> def1 + fin4 is fin4
            True

        Adding with something else than default/override, raises
        ``PlumbingCollision``.

        .. code-block:: pycon

            >>> def1 + Instruction('foo')
            Traceback (most recent call last):
              ...
            plumber.exceptions.PlumbingCollision:
                <default 'None' of None payload=1>
              with:
                <Instruction 'None' of None payload='foo'>

        """
        if self == right:
            return self
        if isinstance(right, default):
            return self
        if isinstance(right, override):
            return right
        if isinstance(right, finalize):
            return right
        raise PlumbingCollision(self, right)

    def __call__(self, dct, derived_members):
        name = self.name
        if name not in dct and name not in derived_members:
            dct[name] = self.payload


class override(Stage1Instruction):
    """Override a class attribute.

    An ``override`` attribute overrides an attribute defined on a base class or
    provided by ``default``, but is overridden by ``finalize`` and attributes
    declared on the plumbing class (implicit ``finalize``).

    The first ``override`` will be picked over later ``override``.

    For default/override/finalize merging see ``__add__`` here,
    ``default.__add__`` and ``finalize.__add__``.
    """

    def __add__(self, right):
        """First override wins against following equal overrides and arbitrary
        defaults.

        .. code-block:: pycon

            >>> ext1 = override(1)
            >>> ext1 + ext1 is ext1
            True

            >>> ext1 + override(1) is ext1
            True

            >>> ext1 + override(2) is ext1
            True

            >>> ext1 + default(2) is ext1
            True

            >>> fin3 = finalize(3)
            >>> ext1 + fin3 is fin3
            True

        Everything except default/override collides.

        .. code-block:: pycon

            >>> ext1 + Instruction(1)
            Traceback (most recent call last):
              ...
            plumber.exceptions.PlumbingCollision:
                <override 'None' of None payload=1>
              with:
                <Instruction 'None' of None payload=1>

        """
        if self == right:
            return self
        if isinstance(right, default):
            return self
        if isinstance(right, override):
            return self
        if isinstance(right, finalize):
            return right
        raise PlumbingCollision(self, right)

    def __call__(self, dct, derived_members):
        if self.name in dct:
            return
        dct[self.name] = self.payload


class finalize(Stage1Instruction):
    """Insist on the final value / finalize the endpoint.

    A ``finalize`` attribute is chosen over all others, two ``finalize``
    collide, declarations on the plumbing class are implicit ``finalize``
    declarations.

    For default/override/finalize merging see ``__add__`` here,
    ``default.__add__`` and ``override.__add__``.
    """

    def __add__(self, right):
        """First override wins against following equal overrides and arbitrary
        defaults.

        .. code-block:: pycon

            >>> fin1 = finalize(1)
            >>> fin1 + fin1 is fin1
            True

            >>> fin1 + finalize(1) is fin1
            True

            >>> fin1 + default(2) is fin1
            True

            >>> fin1 + override(2) is fin1
            True

        Two unequal finalize collide.

        .. code-block:: pycon

            >>> fin1 + finalize(2)
            Traceback (most recent call last):
              ...
            plumber.exceptions.PlumbingCollision:
                <finalize 'None' of None payload=1>
              with:
                <finalize 'None' of None payload=2>

        Everything except default/override collides.

        .. code-block:: pycon

            >>> fin1 + Instruction(1)
            Traceback (most recent call last):
              ...
            plumber.exceptions.PlumbingCollision:
                <finalize 'None' of None payload=1>
              with:
                <Instruction 'None' of None payload=1>

        """
        if self == right:
            return self
        if isinstance(right, default):
            return self
        if isinstance(right, override):
            return self
        raise PlumbingCollision(self, right)

    def __call__(self, dct, derived_members):
        if self.name in dct:
            raise PlumbingCollision('Plumbing class', self)
        dct[self.name] = self.payload


###############################################################################
# Stage2 instructions
###############################################################################

class Stage2Instruction(Instruction):
    """Instructions installed in stage2: so far only plumb."""
    __stage__ = 'stage2'

    def __call__(self, cls):
        """cls is the plumbing class, type finished its work already."""
        raise NotImplementedError  # pragma: no cover


def entrancefor(plumbing_method, next_):
    """An entrance for a plumbing method, given next_.

    The entrance returned is a closure with signature: (self, *args, **kw), it
    wraps a call of plumbing_method curried with next_.
    """
    def entrance(self, *args, **kw):
        return plumbing_method(next_, self, *args, **kw)
    entrance.__doc__ = plumb_str(plumbing_method.__doc__, next_.__doc__)
    entrance.__name__ = plumbing_method.__name__
    return entrance


def plumbingfor(plumbing_method, next_):
    """A plumbing method combining two plumbing methods."""
    def plumbing(next__, self, *args, **kw):
        return plumbing_method(entrancefor(next_, next__), self, *args, **kw)
    plumbing.__doc__ = plumb_str(plumbing_method.__doc__, next_.__doc__)
    plumbing.__name__ = plumbing_method.__name__
    return plumbing


class plumb(Stage2Instruction):
    """Plumbing of strings, methods and properties.

    XXX: support getter, setter, deleter to enable:

        @plumb
        @property
        def foo

        @foo.setter
        def foo
    """

    def __add__(self, right):
        """Add function to pipeline.

        .. code-block:: pycon

            >>> from plumber import plumb

            >>> plb1 = plumb(1)
            >>> plb1 + plumb(1) is plb1
            True

            >>> plb1 + Instruction(1)
            Traceback (most recent call last):
              ...
            plumber.exceptions.PlumbingCollision:
                <plumb 'None' of None payload=1>
              with:
                <Instruction 'None' of None payload=1>

            >>> plumb(lambda x: None) + plumb(property(lambda x: None))
            Traceback (most recent call last):
              ...
            plumber.exceptions.PlumbingCollision:
                <plumb 'None' of None payload=<function <lambda> at 0x...>>
              with:
                <plumb 'None' of None payload=<property object at 0x...>>

        """
        if self == right:
            return self
        if not isinstance(right, plumb):
            raise PlumbingCollision(self, right)
        if not self.ok(self.payload, right.payload):
            raise PlumbingCollision(self, right)
        return plumb(self.plumb(plumbingfor, self.payload, right.payload),
                     name=self.name)

    def ok(self, p1, p2):
        """Check whether we can merge two payloads.

        .. code-block:: pycon

            >>> plumb(1) + plumb(2)
            Traceback (most recent call last):
              ...
            plumber.exceptions.PlumbingCollision:
                <plumb 'None' of None payload=1>
              with:
                <plumb 'None' of None payload=2>

        """
        if isinstance(p1, STR_TYPE):
            return isinstance(p2, STR_TYPE) or p2 is None
        if isinstance(p1, property):
            return isinstance(p2, property)
        if callable(p1):
            return callable(p2)
        return False

    def plumb(self, plbfunc, p1, p2):
        if isinstance(p1, STR_TYPE):
            return plumb_str(p1, p2)
        if isinstance(p1, property):
            # XXX: This should be split up into instructions during part
            # parsing to enable two stages and all instructions
            propfuncs = []
            for x in 'fget', 'fset', 'fdel':
                p1func = getattr(p1, x)
                p2func = getattr(p2, x)
                if p2func is None:
                    propfuncs.append(p1func)
                elif type(p2func) is override:
                    propfuncs.append(p2func.payload)
                else:
                    propfuncs.append(plbfunc(p1func, p2func))
            propfuncs.append(plumb_str(p1.__doc__, p2.__doc__))
            return p1.__class__(*propfuncs)
        if callable(p1):
            return plbfunc(p1, p2)
        # Should never happen
        raise RuntimeError('Unknown plumbing case.')  # pragma: no cover

    def __call__(self, cls):
        # Check for a method on the plumbing class itself.
        next_ = getattr(cls, self.name)
        if not self.ok(self.payload, next_):
            raise PlumbingCollision(self, cls)
        entrance = self.plumb(entrancefor, self.payload, next_)
        setattr(cls, self.name, entrance)


class plumbifexists(plumb):
    """Only plumb, if an end point exists."""

    def __call__(self, cls):
        try:
            super(plumbifexists, self).__call__(cls)
        except AttributeError:
            pass


if ZOPE_INTERFACE_AVAILABLE:
    class _implements(Stage2Instruction):
        """classImplements interfaces.

        .. code-block:: pycon

            >>> from plumber.instructions import _implements

            >>> foo = _implements(('foo',))
            >>> foo == foo
            True

            >>> foo + foo is foo
            True

            >>> foo == _implements(('foo',))
            True

            >>> foo != _implements(('bar',))
            True

            >>> _implements(('foo', 'bar')) == _implements(('bar', 'foo'))
            True

            >>> foo + _implements(('foo',)) is foo
            True

            >>> bar = _implements(('bar',))
            >>> foo + bar
            <_implements '__interfaces__' of None payload=('bar', 'foo')>

            >>> foo + bar == bar + foo
            True

            >>> foo + Instruction('bar')
            Traceback (most recent call last):
              ...
            plumber.exceptions.PlumbingCollision:
                <_implements '__interfaces__' of None payload=('foo',)>
              with:
                <Instruction 'None' of None payload='bar'>

        """
        __name__ = '__interfaces__'

        def __add__(self, right):
            if self == right:
                return self
            if not isinstance(right, _implements):
                raise PlumbingCollision(self, right)
            ifaces = self.payload + right.payload
            return _implements(ifaces)

        def __call__(self, cls):
            if self.payload:
                classImplements(cls, *self.payload)

        @property
        def payload(self):
            if type(self.item) is tuple:
                return tuple(sorted(self.item))
            return tuple(sorted(implementedBy(self.item)))
