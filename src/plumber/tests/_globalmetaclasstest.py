"""A module to test setting a metaclass globally

ATTENTION: we do not recommend this, but you can do it!

Mostly here for understanding what's going on.
"""

from zope.interface import Interface
from zope.interface import implementer

from plumber import plumber
from plumber import Behavior

__metaclass__ = plumber


class IBehavior1(Interface):
    """
    A zope.interface.Interface is not affected by the global ``__metaclass__``.
    ::
        >>> IBehavior1.__class__
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


@implementer(IBehavior1)
class Behavior1(Behavior):
    pass


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

        >>> IBehavior1.implementedBy(ClassReallyUsingAPlumbing)
        True
    """
    __plumbing__ = Behavior1
