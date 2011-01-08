Plumber
=======

A plumber is a metaclass that implements a plumbing system which works
orthogonal to subclassing.


A quick example
---------------

Import of the plumbing decorator for the plumbing methods and the Plumber
metaclass.
::

    >>> from plumber import plumbing
    >>> from plumber import Plumber

A base clase
::

    >>> class Base(object):
    ...     def foo(self):
    ...         print "Base.foo"

Two plugins for the plumbing. The decorator makes the methods part of the
plumbing. They are classmethods of the plugin. Via _next they can call the next
plumbing method in the pipeline.
::

    >>> class Plugin1(object):
    ...     @plumbing
    ...     def foo(cls, _next, self):
    ...         print "Plugin1.foo start"
    ...         _next(self)
    ...         print "Plugin1.foo stop"

    >>> class Plugin2(object):
    ...     @plumbing
    ...     def foo(cls, _next, self):
    ...         print "Plugin2.foo start"
    ...         _next(self)
    ...         print "Plugin2.foo stop"

A class using a plumbing and having Base as base class. The Plumber metaclass
creates the plumbing according to the ``__pipeline__`` attribute.
::

    >>> class ClassWithPlumbing(Base):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1, Plugin2)
    ...
    ...     def foo(self):
    ...         print "ClassWithPlumbing.foo start"
    ...         super(ClassWithPlumbing, self).foo()
    ...         print "ClassWithPlumbing.foo stop"

The plumbing sits in front of the class and its base classes
::

    >>> cwp = ClassWithPlumbing()
    >>> cwp.foo()
    Plugin1.foo start
    Plugin2.foo start
    ClassWithPlumbing.foo start
    Base.foo
    ClassWithPlumbing.foo stop
    Plugin2.foo stop
    Plugin1.foo stop

The plumbing classes are not part of a class' method resolution order.
::

    >>> ClassWithPlumbing.__mro__
    (<class 'ClassWithPlumbing'>,
     <class 'Base'>,
     <type 'object'>)

    >>> issubclass(ClassWithPlumbing, Base)
    True
    >>> issubclass(ClassWithPlumbing, Plugin1)
    False
    >>> issubclass(ClassWithPlumbing, Plugin2)
    False

A class that uses plumbing can be subclassed as usual.
::

    >>> class SubOfClassWithPlumbing(ClassWithPlumbing):
    ...     def foo(self):
    ...         print "SubOfClassWithPlumbing.foo start"
    ...         super(SubOfClassWithPlumbing, self).foo()
    ...         print "SubOfClassWithPlumbing.foo stop"

    >>> subofcwp = SubOfClassWithPlumbing()
    >>> subofcwp.foo()
    SubOfClassWithPlumbing.foo start
    Plugin1.foo start
    Plugin2.foo start
    ClassWithPlumbing.foo start
    Base.foo
    ClassWithPlumbing.foo stop
    Plugin2.foo stop
    Plugin1.foo stop
    SubOfClassWithPlumbing.foo stop

..note:: A class inherits the ``__metaclass__`` declaration from base classes.
The ``Plumber`` metaclass is called for ``ClassWithPlumbing`` **and**
``SubOfClassWithPlumbing``. However, it will only get active for a class that
declares a ``__pipeline__`` itself and otherwise just calls ``type``, the
default metaclass for new-style classes.


A more lengthy explanation
--------------------------

A plumbing consists of plumbing elements that define methods to be used as part
of the plumbing. An object using a plumbing system, declares the Plumber as its
metaclass and a ``__pipeline__`` defining the order of plumbing elements to be
used.

The plumbing system works similar to WSGI (the Web Server Gateway Interface).
It consists of pipelines that are formed of plumbing methods of the listed
classes. For each pipeline an entrance method is created that is called like
every normal method with the general signature of ``def foo(self, **kws)``.
The entrance method will just wrap the first plumbing method.

Plumbing methods receive a wrapper of the next plumbing method. Therefore they
can alter arguments before passing them on to the next plumbing method
(preprocessing the request) and alter the return value of the next plumbing
method (postprocessing the response) before returning it further.

The normal endpoint is determined by ``getattr`` on the class without the
plumbing system. If neither the class itself nor its base classes implement a
corresponding method, a method is created that raises a
``NotImplementedError``. A plumbing method can serve as an endpoint by just not
calling ``_next``, by that it basically implements a new method for the class,
as it were defined on the class. A super call to the class' bases can be made
``super(self.__class__, self).name(**kws)``.

..note:: It is not possible to pass positional arguments to the plumbing system
  and anything behind it, as this is not valid python
  ``def f(foo, *args, bar=None, **kws)``.

  XXX: Please correct me if I am wrong and we will see whether ``*args`` can
  be supported (see also Discussion below).


Nomenclature
------------

The nomenclature is just forming and still inconsistent.

Plumber
    The plumber is the metaclass creating a plumbing system.

plumbing (system)
    The plumbing system is the result of what the Plumber produces. It consists
    of pipelines containing wrapped plumbing methods and is made from plumbing
    classes that are lined up according to the ``__pipeline__`` attribute of a
    class asking for a plumbing system.

plumbing class, plugin, element
    A plumbing class defines plumbing methods and therefore can be used as part
    of a plumbing system.

plumbing decorator
    The plumbing decorator marks a method to be part of the plumbing and makes
    it a classmethod of the class defining it. (See Discussion below for
    plumbing based on non-class methods, i.e. instantiated plumbing classes).

plumbing (method)
    A plumbing method is a classmethod marked by the plumbing decorator.
    Plumbing methods (of different plumbing classes) with the same name form a
    pipeline. The plumber plumbs them together in the order defined by the
    ``__pipeline__`` attribute defined on a class asking for a plumbing system.

pipeline attribute
    The attribute a class uses to define the order of plumbing class to be used
    to create the plumbing.

pipeline
    A row of plumbing methods of the same name.

XXX: we need a name for a class that uses a plumbing system.


Example
-------

Notify plumbing class
---------------------

A plumbing element that prints notifications for its ``__init__`` and
``__setitem__`` methods. A plumbing method is decorated with the ``@plumbing``
decorator, its general signature is ``def foo(cls, _next, self, **kws)``.
All plumbing methods are classmethods, the plumbing class is passed as the
first argument ``cls`` to its methods. The second method ``_next`` wraps the
the next plumbing method of a pipeline and ``self`` is an instance of the class
that uses the plumbing, just what you would expect to be ``self`` in a method
of a normal class.

..attention:: ``self`` is not an instance of the plumbing class, but of the
  class using the plumbing system. The system is designed so the code you write
  in plumbing methods looks as similar as possible to the code you would write
  directly in the class.

XXX: we could wrap self, too (less to write). However, it might enable weird
stuff were you pass something else on to be self. (see Discussion below)

::

    >>> class Notifier(object):
    ...     """Prints notifications before/after setting an item
    ...     """
    ...     @plumbing
    ...     def __init__(cls, _next, self, notify=False, **kws):
    ...         if notify:
    ...             print "%s.__init__: begin with: %s." % \
    ...                     (cls, object.__repr__(self))
    ...         self.notify = notify
    ...         _next(self, **kws)
    ...         if notify:
    ...             print "%s.__init__: end." % (cls,)
    ...
    ...     @plumbing
    ...     def __setitem__(cls, _next, self, key, val):
    ...         if self.notify:
    ...             print "%s.__setitem__: setting %s as %s for %s." % \
    ...                     (cls, val, key, object.__repr__(self))
    ...         _next(self, key, val)
    ...         if self.notify:
    ...             print "%s.__setitem__: done." % (cls,)
    ...
    ...     @plumbing
    ...     def foo(cls, _next, self):
    ...         # the base classes do not provide an end point, but we are.
    ...         return "Notifier.foo is end point."
    ...
    ...     @plumbing
    ...     def bar(cls, _next, self):
    ...         # bar is not an end point and will result in
    ...         # NotImplementedError, as the base classes will not provide an
    ...         # end point
    ...         _next(self)

    >>> class NotifyDict(dict):
    ...     """A dictionary that prints notification on __setitem__
    ...     """
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Notifier,)
    ...
    ...     def __init__(self):
    ...         print "%s.__init__: begin" % (self.__class__,)
    ...         super(NotifyDict, self).__init__()
    ...         print "%s.__init__: end" % (self.__class__,)

The methods defined on the class directly, in this case ``__init__`` are called
as the innermost methods and build the end point of a pipeline.
::

    >>> ndict = NotifyDict(notify=True)
    <class 'Notifier'>.__init__: begin with: <NotifyDict object at ...>.
    <class 'NotifyDict'>.__init__: begin
    <class 'NotifyDict'>.__init__: end
    <class 'Notifier'>.__init__: end.

The paremeter set by the plumbing __init__ made it onto the created object.
::

    >>> ndict.notify
    True

If a method is not present on the class itself, it will be looked up on the
base classes, actually ``getattr`` on the class is used, before the plumbing
system is installed. If that getattr fails and no plumbing class provided an
end point, a ``NotImplementedError`` will be raised (see below in case of
``ndict.foo`` and ``ndict.bar``.
::

    >>> ndict['foo'] = 1
    <class 'Notifier'>.__setitem__: setting 1 as foo for <NotifyDict object at ...>.
    <class 'Notifier'>.__setitem__: done.

    >>> ndict['foo']
    1

And it is really the one used by the plumbing __setitem__ to determine whether
to print notifications.
::

    >>> ndict.notify = False
    >>> ndict['bar'] = 2
    >>> ndict['bar']
    2

Even though the base class ``dict`` does not provide an end point for ``foo``,
the Notifier plumbing class does and we cann call ``ndict.foo()``.
::

    >>> ndict.foo()
    'Notifier.foo is end point.'

The base class ``dict`` does not provide an end point for ``bar`` and neither
does our plumbing class.
::

    >>> ndict.bar()
    Traceback (most recent call last):
    ...
    NotImplementedError


A prefixer plumbing
-------------------

::
    >>> class Prefixer(object):
    ...     """Prefixes keys
    ...     """
    ...     @plumbing
    ...     def __init__(cls, _next, self, prefix=None, **kws):
    ...         print "%s.__init__: begin with: %s." % (
    ...                 cls, object.__repr__(self))
    ...         self.prefix = prefix
    ...         _next(self, **kws)
    ...         print "%s.__init__: end." % (cls,)
    ...
    ...     @classmethod
    ...     def prefix(cls, self, key):
    ...         return self.prefix + key
    ...
    ...     @classmethod
    ...     def unprefix(cls, self, key):
    ...         if not key.startswith(self.prefix):
    ...             raise KeyError(key)
    ...         return key.lstrip(self.prefix)
    ...
    ...     @plumbing
    ...     def __delitem__(cls, _next, self, key):
    ...         _next(self, cls.unprefix(self, key))
    ...
    ...     @plumbing
    ...     def __getitem__(cls, _next, self, key):
    ...         return _next(self, cls.unprefix(self, key))
    ...
    ...     @plumbing
    ...     def __iter__(cls, _next, self):
    ...         for key in _next(self):
    ...             yield cls.prefix(self, key)
    ...
    ...     @plumbing
    ...     def __setitem__(cls, _next, self, key, val):
    ...         print "%s.__setitem__: begin with: %s." % (
    ...                 cls, object.__repr__(self))
    ...         try:
    ...             key = cls.unprefix(self, key)
    ...         except KeyError:
    ...             raise KeyError("Key '%s' does not match prefix '%s'." % \
    ...               (key, self.prefix))
    ...         _next(self, key, val)

In the above example it would not be possible for a subclass of
NotifyPrefixDict to override the prefix and unprefix methods as they are not in
NotifyPrefixDict's MRO but are defined on the plumbing class and called via
plumbing methods. It feels, that for such purposes no classmethods on the
plumbing element should be used. By that it is possible for somebody
subclassing us, to override these methods.

    >>> class NotifyPrefixDict(dict):
    ...     """A dictionary that prints notifications and has prefixed keys
    ...     """
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Notifier, Prefixer)

XXX: This collides with dict __init__ signature: dict(foo=1, bar=2)
--> creating a subclass of dict that does __init__ translation might work:
data=() - eventually a specialized plugin, but let's keep this simple for now.

    >>> npdict = NotifyPrefixDict(prefix='pre-', notify=True)
    <class 'Notifier'>.__init__: begin with: <NotifyPrefixDict object at ...>.
    <class 'Prefixer'>.__init__: begin with: <NotifyPrefixDict object at ...>.
    <class 'Prefixer'>.__init__: end.
    <class 'Notifier'>.__init__: end.

    >>> npdict['foo'] = 1
    Traceback (most recent call last):
    ...
    KeyError: "Key 'foo' does not match prefix 'pre-'."

    >>> npdict.keys()
    []

    >>> npdict['pre-foo'] = 1
    <class 'Notifier'>.__setitem__: setting 1 as pre-foo for <NotifyPrefixDict object at ...>.
    <class 'Prefixer'>.__setitem__: begin with: <NotifyPrefixDict object at ...>.
    <class 'Notifier'>.__setitem__: done.

    >>> npdict['pre-foo']
    1

    >>> [x for x in npdict]
    ['pre-foo']

keys() is not handle by the prefixer, the one provided by dict is used and
therefore the internal key names are shown.

    >>> npdict.keys()
    ['foo']

    >>> class PrefixNotifyDict(dict):
    ...     """like NotifyPrefix, but different order
    ...     """
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Prefixer, Notifier)

    >>> rev_npdict = PrefixNotifyDict(prefix='_pre-', notify=True)
    <class 'Prefixer'>.__init__: begin with: <PrefixNotifyDict object at ...>.
    <class 'Notifier'>.__init__: begin with: <PrefixNotifyDict object at ...>.
    <class 'Notifier'>.__init__: end.
    <class 'Prefixer'>.__init__: end.

Notifier show now unprefixed key, as it is behind the prefixer

    >>> rev_npdict['_pre-bar'] = 1
    <class 'Prefixer'>.__setitem__: begin with: <PrefixNotifyDict object at ...>.
    <class 'Notifier'>.__setitem__: setting 1 as bar for <PrefixNotifyDict object at ...>.
    <class 'Notifier'>.__setitem__: done.


    >>> rev_npdict['_pre-bar']
    1


Subclassing plumbing elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


zope.interface support
----------------------

The plumber does not depend on ``zope.interface`` but is aware of it. That
means it will try to import it and if available will check plumbing classes
for implemented interfaces and will make the new class implement them.

    >>> from zope.interface import Interface
    >>> from zope.interface import classImplements
    >>> from zope.interface import implements

A base class with an interface.
::

    >>> class IBase(Interface):
    ...     pass

    >>> class Base(object):
    ...     implements(IBase)

    >>> IBase.implementedBy(Base)
    True

Two plugins with corresponding interfaces, one with a base class that also
implements an interface.
::

    >>> class IPlugin1(Interface):
    ...     pass

    >>> class Plugin1(object):
    ...     implements(IPlugin1)

    >>> class IPlugin2Base(Interface):
    ...     pass

    >>> class Plugin2Base(object):
    ...     implements(IPlugin2Base)

    >>> class IPlugin2(Interface):
    ...     pass

    >>> class Plugin2(Plugin2Base):
    ...     implements(IPlugin2)

    >>> IPlugin1.implementedBy(Plugin1)
    True
    >>> IPlugin2Base.implementedBy(Plugin2Base)
    True
    >>> IPlugin2Base.implementedBy(Plugin2)
    True
    >>> IPlugin2.implementedBy(Plugin2)
    True

A class based on ``Base`` using a plumbing of ``Plugin1`` and ``Plugin2`` and
implementing ``IClassWithPlumbing``.
::

    >>> class IClassWithPlumbing(Interface):
    ...     pass

    >>> class ClassWithPlumbing(Base):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1, Plugin2)
    ...     implements(IClassWithPlumbing)

The directly declared and inherited interfaces are implemented.
::

    >>> IClassWithPlumbing.implementedBy(ClassWithPlumbing)
    True
    >>> IBase.implementedBy(ClassWithPlumbing)
    True

The interfaces implemented by the used plumbing classes are also implemented.
::

    >>> IPlugin1.implementedBy(ClassWithPlumbing)
    True
    >>> IPlugin2.implementedBy(ClassWithPlumbing)
    True
    >>> IPlugin2Base.implementedBy(ClassWithPlumbing)
    True

An instance of the class provides the interfaces.
::

    >>> cwp = ClassWithPlumbing()

    >>> IClassWithPlumbing.providedBy(cwp)
    True
    >>> IBase.providedBy(cwp)
    True
    >>> IPlugin1.providedBy(cwp)
    True
    >>> IPlugin2.providedBy(cwp)
    True
    >>> IPlugin2Base.providedBy(cwp)
    True

The reasoning behind this is, that the plumbing classes are behaving as close
as possible to base classes of our class, but without using subclassing.
For an additional maybe future approach see Discussion.


Discussions
-----------

Where is the plumbing
~~~~~~~~~~~~~~~~~~~~~
It is in front of the class and its MRO. If you feel it should be between the
class and its base classes, consider subclassing the class that uses the
plumbing system and put your code there. If you have a strong point why this is
not a solution, please let us know. However, the point must be stronger than
saving 3 lines of which two are pep8-conform whitespace.

Signature of _next function
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Currently ``self`` needs to be passed to the ``_next`` function. This could be
wrapped, too. However, it might enable cool stuff, because you can decide to
pass something else than self to be processed further.

Implementation of this would slightly increase the complexity in the plumber,
result in less flexibility, but save passing ``self`` to ``_next``.

Instance based plumbing system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
At various points it felt tempting to be able to instantiate plumbing elements
to configure them. For that we need ``__init__``, which woul mean that plumbing
``__init__`` would need a different name, eg. ``plb_``-prefix. Consequently
this could then be done for all plumbing methods instead of decorating them.
The decorator is really just used for marking them and turning them into
classmethods. The plumbing decorator is just a subclass of the classmethod
decorator.

Reasoning why currently the methods are not prefixed and are classmethods:
Plumbing elements are simply not meant to be normal classes. Their methods have
the single purpose to be called as part of some other class' method calls,
never directly. Configuration of plumbing elements can either be achieved by
subclassing them or by putting the configuration on the objects/class they are
used for.

The current system is slim, clear and easy to use. An instance based plumbing
system would be far more complex. It could be implemented to exist alongside
the current system. But it won't be implemented by us, without seeing a real use
case first.

Different zope.interface.Interfaces for plumbing and created class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A different approach to the currently implemented system is having different
interfaces for the plugins and the class that is created.
::

    #    >>> class IPlugin1Behaviour(Interface):
    #    ...     pass
    #
    #    >>> class Plugin1(object):
    #    ...     implements(IPlugin1)
    #    ...     interfaces = (IPlugin1Behaviour,)
    #
    #    >>> class IPlugin2(Interface):
    #    ...     pass
    #
    #    >>> class Plugin2(object):
    #    ...     implements(IPlugin2)
    #    ...     interfaces = (IPlugin2Behaviour,)
    #
    #    >>> IUs.implementedBy(Us)
    #    True
    #    >>> IBase.implementedBy(Us)
    #    True
    #    >>> IPlugin1.implementedBy(Us)
    #    False
    #    >>> IPlugin2.implementedBy(Us)
    #    False
    #    >>> IPlugin1Behaviour.implementedBy(Us)
    #    False
    #    >>> IPlugin2Behaviour.implementedBy(Us)
    #    False

Same reasoning as before: up to now unnecessary complexity. It could make sense
in combination with an instance based plumbing system and could be implemented
as part of it alongside the current class based system.

Implicit subclass generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Currently the whole plumbing system is implemented within one class that is
based on the base classes defined in the class declaration. During class
creation the plumber determines all functions involved in the plumbing,
generates pipelines of methods and plumbs them together.

An alternative approach would be to take one plumbing elements after another
and create a subclass chain. However, I currently don't know how this could be
achieved, believe that it is not possible and think that the current approach
is better.

Positional arguments
~~~~~~~~~~~~~~~~~~~~
Currently, it is not possible to pass positional arguments ``*args`` to
plumbing methods and therefore everything behind the plumbing system. In
python, this syntax is not valid ``def f(foo, *args, bar=1, **kws)``. If you
have any idea how to support positional arguments, pleas let us know.


Contributors
------------

- Florian Friesdorf <flo@chaoflow.net>
- Robert Niederreiter <rnix@squarewave.at>
- Attila Oláh
- WSGI
- #python


Changes
-------

- initial [chaoflow, 2011-01-04]


TODO
----

- traceback should show in which plumbing class we are, not something inside
  the plumber. yafowil is doing it. jensens: would you be so kind.
