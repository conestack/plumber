"""A module to test setting a metaclass globally

ATTENTION: we do not recommend this, but you can do it!

Mostly here for understanding what's going on.
"""

from zope.interface import Interface
from zope.interface import implements

from plumber import Plumber

__metaclass__ = Plumber


class IPlugin1(Interface):
    """
    A zope.interface.Interface is not affected by the global ``__metaclass__``.
    ::
        >>> IPlugin1.__class__
        <class 'zope.interface.interface.InterfaceClass'>
    """
    pass


class Plugin1:
    """
    A global meta-class declaration makes all classes at least new-style
    classes, even when not subclassing subclasses.
    ::
        >>> Plugin1.__class__
        <class 'plumber._plumber.Plumber'>

        >>> issubclass(Plugin1, object)
        True
    """
    implements(IPlugin1)


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
        <class 'plumber._plumber.Plumber'>

        >>> issubclass(ClassReallyUsingAPlumbing, object)
        True

        >>> IPlugin1.implementedBy(ClassReallyUsingAPlumbing)
        True
    """
    __pipeline__ = (Plugin1,)
