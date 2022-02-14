"""A module to test setting a metaclass globally

ATTENTION: we do not recommend this, but you can do it!

Mostly here for understanding what's going on.
"""
from plumber import Behavior
from plumber import plumber
from plumber import plumbing
from zope.interface import Interface
from zope.interface import implementer


__metaclass__ = plumber


class IBehavior1(Interface):
    """A zope.interface.Interface is not affected by the global
    ``__metaclass__``.

    .. code-block:: pycon

        >>> IBehavior1.__class__
        <class 'zope.interface.interface.InterfaceClass'>

    """


class Foo:
    """A global meta-class declaration makes all classes at least new-style
    classes, even when not subclassing subclasses.

    .. code-block:: pycon

        >>> Foo.__class__
        <class 'plumber.plumber.plumber'>

        >>> issubclass(Foo, object)
        True

    """


@implementer(IBehavior1)
class Behavior1(Behavior):
    pass


class ClassMaybeUsingAPlumbing(object):
    """If subclassing object, the global metaclass declaration is ignored.

    .. code-block:: pycon

        >>> ClassMaybeUsingAPlumbing.__class__
        <type 'type'>

    """


@plumbing(Behavior1)
class ClassReallyUsingAPlumbing:
    """A plumbing class.

    .. code-block:: pycon

        >>> ClassReallyUsingAPlumbing.__class__
        <class 'plumber.plumber.plumber'>

        >>> issubclass(ClassReallyUsingAPlumbing, object)
        True

        >>> IBehavior1.implementedBy(ClassReallyUsingAPlumbing)
        True

    """


class BCClassReallyUsingAPlumbing:
    """A plumbing class setting behaviors the B/C method.

    .. code-block:: pycon

        >>> BCClassReallyUsingAPlumbing.__class__
        <class 'plumber.plumber.plumber'>

        >>> issubclass(BCClassReallyUsingAPlumbing, object)
        True

        >>> IBehavior1.implementedBy(BCClassReallyUsingAPlumbing)
        True

    """
    __plumbing__ = Behavior1
