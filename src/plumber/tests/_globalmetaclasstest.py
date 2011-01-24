"""A module to test setting a metaclass globally

ATTENTION: we do not recommend this, but you can do it!

Mostly here for understanding what's going on.
"""

from zope.interface import Interface
from zope.interface import implements

from plumber import plumber
from plumber import Part

__metaclass__ = plumber


class IPart1(Interface):
    """
    A zope.interface.Interface is not affected by the global ``__metaclass__``.
    ::
        >>> IPart1.__class__
        <class 'zope.interface.interface.InterfaceClass'>
    """
    pass


class Foo:
    """
    A global meta-class declaration makes all classes at least new-style
    classes, even when not subclassing subclasses.
    ::
        >>> Foo.__class__
        <class 'plumber._plumber.plumber'>

        >>> issubclass(Foo, object)
        True
    """


class Part1(Part):
    implements(IPart1)


class ClassMaybeUsingAPlumbing(object):
    """
    If subclassing object, the global metaclass declaration is ignored.
    ::
        >>> ClassMaybeUsingAPlumbing.__class__
        <type 'type'>
    """


class ClassReallyUsingAPlumbing:
    """
        >>> ClassReallyUsingAPlumbing.__class__
        <class 'plumber._plumber.plumber'>

        >>> issubclass(ClassReallyUsingAPlumbing, object)
        True

        >>> IPart1.implementedBy(ClassReallyUsingAPlumbing)
        True
    """
    __plumbing__ = Part1
