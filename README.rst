Plumber
=======

Plumber is a metaclass that implements a plumbing system which works orthogonal
to subclassing. A class declares the plumber as its metaclass and a pipeline of
plugins that form the plumbing system. Plugins can extend classes as if the
code was declared on the class itself (``extend`` decorator), provide default
values for class variables (``default`` decorator) and form chains of methods
(``plumb`` decorator) that pre-process parameters before passing them to the
next method and post-process results before passing them to the previous method
(similar to WSGI pipelines).

Why not just use sub-classing? see Motivation.
::
    >>> from plumber import Plumber
    >>> from plumber import default
    >>> from plumber import extend
    >>> from plumber import plumb

The plumber is aware of ``zope.interface`` but does not require it (see
``zope.interface support``)

XXX: write about property support

XXX: use reStructured section references, does something like that exist?


Plumbing chains
---------------

XXX: diagram how a plumbing chain works

Plumbing chains and usual subclassing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A class that will serve as normal base class for our plumbing.
::
    >>> class Base(object):
    ...     def foo(self):
    ...         print "Base.foo"

Two plugins for the plumbing: the ``plumb`` decorator makes the methods part of
the plumbing, they are classmethods of the plugin declaring them ``plb``, via
``_next`` they call the next method and ``self`` is an instance of the
plumbing.

..attention:: ``self`` is not an instance of the plugin class, but an
  instance of plumbing class. The system is designed so the code you write in
  plumbing methods looks as similar as possible to the code you would write
  directly on the class.
::
    >>> class Plugin1(object):
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         print "Plugin1.foo start"
    ...         _next(self)
    ...         print "Plugin1.foo stop"

    >>> class Plugin2(object):
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         print "Plugin2.foo start"
    ...         _next(self)
    ...         print "Plugin2.foo stop"

A plumbing based on ``Base`` and using the plugins ``Plugin1`` and ``Plugin2``.
::
    >>> class PlumbingClass(Base):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1, Plugin2)
    ...
    ...     def foo(self):
    ...         print "PlumbingClass.foo start"
    ...         super(PlumbingClass, self).foo()
    ...         print "PlumbingClass.foo stop"

Methods provided by the plugins sit in front of methods declared by the class
and its base classes.
::
    >>> plumbing = PlumbingClass()
    >>> plumbing.foo()
    Plugin1.foo start
    Plugin2.foo start
    PlumbingClass.foo start
    Base.foo
    PlumbingClass.foo stop
    Plugin2.foo stop
    Plugin1.foo stop

The plugins are not in the class' method resolution order.
::
    >>> PlumbingClass.__mro__
    (<class 'PlumbingClass'>,
     <class 'Base'>,
     <type 'object'>)

    >>> issubclass(PlumbingClass, Base)
    True
    >>> issubclass(PlumbingClass, Plugin1)
    False
    >>> issubclass(PlumbingClass, Plugin2)
    False

The plumbing can be subclassed like a normal class.
::
    >>> class SubOfPlumbingClass(PlumbingClass):
    ...     def foo(self):
    ...         print "SubOfPlumbingClass.foo start"
    ...         super(SubOfPlumbingClass, self).foo()
    ...         print "SubOfPlumbingClass.foo stop"

    >>> subofplumbing = SubOfPlumbingClass()
    >>> subofplumbing.foo()
    SubOfPlumbingClass.foo start
    Plugin1.foo start
    Plugin2.foo start
    PlumbingClass.foo start
    Base.foo
    PlumbingClass.foo stop
    Plugin2.foo stop
    Plugin1.foo stop
    SubOfPlumbingClass.foo stop

..note:: A class inherits the ``__metaclass__`` declaration from base classes.
  The ``Plumber`` metaclass is called for ``PlumbingClass`` **and**
  ``SubOfPlumbingClass``. However, it will only get active for a class that
  declares a ``__pipeline__`` itself and otherwise just calls ``type``, the
  default metaclass for new-style classes.


Passing parameters to methods in a plumbing chain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parameters to plumbing methods are passed in via keyword arguments - there is
no sane way to do this via positional arguments (see section Default
attributes for application to ``__init__`` plumbing).
::
    >>> class Plugin1(object):
    ...     @plumb
    ...     def foo(plb, _next, self, *args, **kw):
    ...         print "Plugin1.foo: args=%s" % (args,)
    ...         print "Plugin1.foo: kw=%s" % (kw,)
    ...         self.p1 = kw.pop('p1', None)
    ...         _next(self, *args, **kw)

    >>> class Plugin2(object):
    ...     @plumb
    ...     def foo(plb, _next, self, *args, **kw):
    ...         print "Plugin2.foo: args=%s" % (args,)
    ...         print "Plugin2.foo: kw=%s" % (kw,)
    ...         self.p2 = kw.pop('p2', None)
    ...         _next(self, *args, **kw)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1, Plugin2)
    ...     def foo(self, *args, **kw):
    ...         print "PlumbingClass.foo: args=%s" % (args,)
    ...         print "PlumbingClass.foo: kw=%s" % (kw,)

The plumbing plugins pick what they need, the remainging keywords and all
positional arguments are just passed through to the plumbing class.
::
    >>> foo = PlumbingClass()
    >>> foo.foo('blub', p1='p1', p2='p2', plumbing='plumbing')
    Plugin1.foo: args=('blub',)
    Plugin1.foo: kw={'p2': 'p2', 'plumbing': 'plumbing', 'p1': 'p1'}
    Plugin2.foo: args=('blub',)
    Plugin2.foo: kw={'p2': 'p2', 'plumbing': 'plumbing'}
    PlumbingClass.foo: args=('blub',)
    PlumbingClass.foo: kw={'plumbing': 'plumbing'}


End-points for plumbing chains
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Plumbing chains need a normal method to serve as end-point.
::
    >>> class Plugin1(object):
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         pass

    >>> class PlumbingClass(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1,)
    Traceback (most recent call last):
      ...
    AttributeError: type object 'PlumbingClass' has no attribute 'foo'

It is looked up on the class with ``getattr``, after the plumbing pipeline is
processed, but before it is installed on the class.

It can be provided by the plumbing class itself.
::
    >>> class Plugin1(object):
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         print "Plugin1.foo start"
    ...         _next(self)
    ...         print "Plugin1.foo stop"

    >>> class PlumbingClass(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1,)
    ...
    ...     def foo(self):
    ...         print "PlumbingClass.foo"

    >>> plumbing = PlumbingClass().foo()
    Plugin1.foo start
    PlumbingClass.foo
    Plugin1.foo stop

It can be provided by a base class of the plumbing class.
::
    >>> class Base(object):
    ...     def foo(self):
    ...         print "Base.foo"

    >>> class Plugin1(object):
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         print "Plugin1.foo start"
    ...         _next(self)
    ...         print "Plugin1.foo stop"

    >>> class PlumbingClass(Base):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1,)

    >>> plumbing = PlumbingClass().foo()
    Plugin1.foo start
    Base.foo
    Plugin1.foo stop

Further it can be provided by a plumbing plugin with the ``default`` or
``extend`` decorators (see Extending classes, an alternative to mixins), it
will be put on the plumbing class, before the end point it looked up and
therefore behaves exactly like the method would be declared on the class
itself.


XXX: Properties
~~~~~~~~~~~~~~~


Extending classes through plumbing, an alternative to mixins
------------------------------------------------------------

Why? It's faster - yet to be proven.

Extending a class
~~~~~~~~~~~~~~~~~
A plugin can put arbitrary attributes onto a class as if they were declared on it.
::
    >>> class Plugin1(object):
    ...     foo = extend(False)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1,)

The attribute is defined on the class, setting it on an instance will store the
value in the instance's ``__dict__``.
::
    >>> PlumbingClass.foo
    False
    >>> plumbing = PlumbingClass()
    >>> plumbing.foo
    False
    >>> plumbing.foo = True
    >>> plumbing.foo
    True
    >>> PlumbingClass.foo
    False

If the attribute collides with one already declared on the class, an exception
is raised.
::
    >>> class Plugin1(object):
    ...     foo = extend(False)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1,)
    ...     foo = False
    Traceback (most recent call last):
      ...
    PlumbingCollision: foo

XXX: increase verbosity of exception

Also, if two plugins try to extend an attribute with the same name, an
exception is raised. The situation before processing the second plugin is
exactly as if the method was declared on the class itself.
::
    >>> class Plugin1(object):
    ...     foo = extend(False)

    >>> class Plugin2(object):
    ...     foo = extend(False)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1, Plugin2)
    Traceback (most recent call last):
      ...
    PlumbingCollision: foo

Extended methods close pipelines, adding a plumbing method afterwards raises an
exception.
::
    >>> class Plugin1(object):
    ...     @extend
    ...     def foo(self):
    ...         pass

    >>> class Plugin2(object):
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         pass

    >>> class PlumbingClass(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1, Plugin2)
    Traceback (most recent call last):
      ...
    PlumbingCollision: foo

Extending a method needed by a plugin earlier in the chain works.
::
    >>> class Plugin1(object):
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         print "Plugin1.foo start"
    ...         _next(self)
    ...         print "Plugin1.foo stop"

    >>> class Plugin2(object):
    ...     @extend
    ...     def foo(self):
    ...         print "Plugin2.foo"

    >>> class PlumbingClass(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1, Plugin2)

    >>> PlumbingClass().foo()
    Plugin1.foo start
    Plugin2.foo
    Plugin1.foo stop

It is possible to make super calls from within the method added by the plugin.
::
    >>> class Base(object):
    ...     def foo(self):
    ...         print "Base.foo"

    >>> class Plugin1(object):
    ...     @extend
    ...     def foo(self):
    ...         print "Plugin1.foo start"
    ...         super(self.__class__, self).foo()
    ...         print "Plugin1.foo stop"

    >>> class PlumbingClass(Base):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1,)

    >>> plumbing = PlumbingClass()
    >>> plumbing.foo()
    Plugin1.foo start
    Base.foo
    Plugin1.foo stop

Extension is used if a plugin relies on a specific attribute value, most common
the case with functions. If a plugin provides a setting it uses a default
value (see next section).

Default attributes
~~~~~~~~~~~~~~~~~~
Plugins that use parameters, provide defaults that are overridable. Further it
should enable setting these parameters through a ``__init__`` plumbing method.
::
    >>> class Plugin1(object):
    ...     foo = default(False)
    ...     @plumb
    ...     def __init__(plb, _next, self, *args, **kw):
    ...         if 'foo' in kw:
    ...             self.foo = kw.pop('foo')
    ...         _next(self, *args, **kw)

    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1,)
    ...     def __init__(self, bar=None):
    ...         self.bar = bar

The default value is set in the class' ``__dict__``.
::
    >>> Plumbing.foo
    False
    >>> plumbing = Plumbing()
    >>> plumbing.foo
    False
    >>> 'foo' in plumbing.__dict__
    False

Setting the value on the instance is persistent and the class' value is
untouched.
::
    >>> plumbing.foo = True
    >>> plumbing.foo
    True
    >>> Plumbing.foo
    False

Values can be provided to ``__init__``.
::
    >>> plumbing = Plumbing(bar=42, foo=True)
    >>> plumbing.foo
    True
    >>> Plumbing.foo
    False
    >>> plumbing.bar
    42

The first plugin prodiving a default value is taken, later defaults are
ignored.
::
    >>> class One(object):
    ...     foo = default(1)

    >>> class Two(object):
    ...     foo = default(2)

    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (One, Two)

    >>> Plumbing.foo
    1

    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Two, One)

    >>> Plumbing.foo
    2

An attribute declared on the class overwrites ``default`` attributes.
::
    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (One, Two)
    ...     foo = None

    >>> print Plumbing.foo
    None

``Extend`` overrules ``default``.
::
    >>> class Default(object):
    ...     foo = default('default')

    >>> class Extend(object):
    ...     foo = extend('extend')

    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Extend, Default)

    >>> Plumbing.foo
    'extend'

    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Default, Extend)

    >>> Plumbing.foo
    'extend'

    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Default, Extend, Default)

    >>> Plumbing.foo
    'extend'

``default`` does not interfere with ``extend`` collision detection.
::
    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Default, Extend, Default, Extend, Default)
    Traceback (most recent call last):
      ...
    PlumbingCollision: foo

``plumb`` and either ``default`` or ``extend`` collide.
::
    >>> class Default(object):
    ...     foo = default(None)

    >>> class Extend(object):
    ...     foo = extend(None)

    >>> class Plumb(object):
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         pass

    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Default, Plumb)
    Traceback (most recent call last):
      ...
    PlumbingCollision: foo

    >>> class Plumbing(object):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Extend, Plumb)
    Traceback (most recent call last):
      ...
    PlumbingCollision: foo


Docstrings of plumbing methods and plugins
------------------------------------------

Two plugins and a plumbing using them, one plumbing chain and ``__doc__``
declared on the classes and the classes' methdods.
::
    >>> class P1(object):
    ...     """P1
    ...     """
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         """P1.foo
    ...         """

    >>> class P2(object):
    ...     """P2
    ...     """
    ...     @plumb
    ...     def foo(plb, _next, self):
    ...         """P2.foo
    ...         """

    >>> class Plumbing(object):
    ...     """Plumbing
    ...     """
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (P1, P2)
    ...
    ...     def foo(self):
    ...         """Plumbing.foo
    ...         """

The class' docstring is generated from the ``__doc__`` declared on the plumbing
class followed by plugin classes' ``__doc__`` in reverse order.
::
    >>> print Plumbing.__doc__
    Plumbing
    <BLANKLINE>
    P2
    <BLANKLINE>
    P1
    <BLANKLINE>

Docstrings for plumbing chains are generated alike.
::
    >>> print Plumbing.foo.__doc__
    Plumbing.foo
    <BLANKLINE>
    P2.foo
    <BLANKLINE>
    P1.foo
    <BLANKLINE>


zope.interface support
----------------------

The plumber does not depend on ``zope.interface`` but is aware of it. That
means it will try to import it and if available will check plumbing classes
for implemented interfaces and will make the new class implement them, too.
::

    >>> from zope.interface import Interface
    >>> from zope.interface import implements

A class with an interface that will serve as base.
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
implementing ``IPlumbingClass``.
::

    >>> class IPlumbingClass(Interface):
    ...     pass

    >>> class PlumbingClass(Base):
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Plugin1, Plugin2)
    ...     implements(IPlumbingClass)

The directly declared and inherited interfaces are implemented.
::

    >>> IPlumbingClass.implementedBy(PlumbingClass)
    True
    >>> IBase.implementedBy(PlumbingClass)
    True

The interfaces implemented by the used plumbing classes are also implemented.
::

    >>> IPlugin1.implementedBy(PlumbingClass)
    True
    >>> IPlugin2.implementedBy(PlumbingClass)
    True
    >>> IPlugin2Base.implementedBy(PlumbingClass)
    True

An instance of the class provides the interfaces.
::

    >>> plumbing = PlumbingClass()

    >>> IPlumbingClass.providedBy(plumbing)
    True
    >>> IBase.providedBy(plumbing)
    True
    >>> IPlugin1.providedBy(plumbing)
    True
    >>> IPlugin2.providedBy(plumbing)
    True
    >>> IPlugin2Base.providedBy(plumbing)
    True

The reasoning behind this is: the plumbing classes are behaving as close as
possible to base classes of our class, but without using subclassing.  For an
additional maybe future approach see Discussion.


A more lengthy explanation
--------------------------

XXX:
A plumbing consists of plumbing elements that define methods to be used as part
of the plumbing. An object using a plumbing system, declares the Plumber as its
metaclass and a ``__pipeline__`` defining the order of plumbing elements to be
used.

The plumbing system works similar to WSGI (the Web Server Gateway Interface).
It consists of pipelines that are formed of plumbing methods of the listed
classes. For each pipeline an entrance method is created that is called like
every normal method with the general signature of ``def foo(self, **kw)``.
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
``super(self.__class__, self).name(**kw)``.
XXX

Nomenclature
------------

The nomenclature is just forming and still inconsistent.

Plumber
    The plumber is the metaclass creating a plumbing system.

plumbing (system)
    A plumbing is the result of what the Plumber produces. It is built of
    methods declared on base classes, the plumbing class and plumbing plugins
    according to ``default``, ``extend`` and ``plumb`` directives. Plugins
    involved are listed in a class' ``__pipeline__`` attribute.

plumbing class
    Synonymous for plumbing system, but sometimes also only the class that asks
    to be turned into a plumbing, esp. when referring to attributes declared on
    it.

(plumbing) plugin / plugin class
    A plumbing plugin provides attributes to be used for the plumbing through
    ``default``, ``extend`` and ``plumb`` declarations.

``default`` decorator
    Instruct the plumber to set a default value: first default wins, ``extend``
    and declaration on plumbing class takes precedence.

``extend`` decorator
    Instruct the plumber to set an attribute on the plumbing: ``extend``
    overrides ``default``, two ``extend`` collide.

``plumb`` decorator
    Instruct the plumber to make a function part of a plumbing chain and turns
    the function into a classmethod bound to the plumbing plugin declaring it
    and having a signature of: ``def foo(plb, _next, self, *args, **kw)``.
    ``plb`` is the plugin class declaring it, ``_next`` a wrapper for the next
    method in chain and ``self`` and instance of the plumbing

plumbing chain
    The methods of a pipeline with the same name plumbed together. The entrance
    and end-point have the signature of normal methods: ``def foo(self, *args,
    **kw)``

pipeline attribute
    The attribute a class uses to define the order of plumbing class to be used
    to create the plumbing.


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

Dynamic Plumbing
~~~~~~~~~~~~~~~~
The plumber could replace the ``__pipeline__`` attribute with a property of the
same name. Changing the attribute during runtime would result in a plumbing
specific to the object. A plumbing cache could further be used to reduce the
number of plumbing chains in case of many dynamic plumbings.


Test Coverage
-------------

XXX: automatic update of coverage report

Summary
~~~~~~~
::
    lines   cov%   module   (path)
        4   100%   plumber.__init__
       16   100%   plumber._globalmetaclasstest
       76    97%   plumber._plumber
       15    93%   plumber.tests

Detailed
~~~~~~~~
Is this sane to have here?

``parts/coverage/plumber._globalmetaclasstest.cover``:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
           """A module to test setting a metaclass globally

           ATTENTION: we do not recommend this, but you can do it!

           Mostly here for understanding what's going on.
        1: """

        1: from zope.interface import Interface
        1: from zope.interface import implements

        1: from plumber import Plumber

        1: __metaclass__ = Plumber


        2: class IPlugin1(Interface):
               """
               A zope.interface.Interface is not affected by the global ``__metaclass__``.
               ::
                   >>> IPlugin1.__class__
                   <class 'zope.interface.interface.InterfaceClass'>
        1:     """
        1:     pass


        2: class Plugin1:
               """
               A global meta-class declaration makes all classes at least new-style
               classes, even when not subclassing subclasses.
               ::
                   >>> Plugin1.__class__
                   <class 'plumber._plumber.Plumber'>

                   >>> issubclass(Plugin1, object)
                   True
        1:     """
        1:     implements(IPlugin1)


        2: class ClassMaybeUsingAPlumbing(object):
               """
               If subclassing object, the global metaclass declaration is ignored.
               ::
                   >>> ClassMaybeUsingAPlumbing.__class__
                   <type 'type'>
        1:     """


        2: class ClassReallyUsingAPlumbing:
               """
                   >>> ClassReallyUsingAPlumbing.__class__
                   <class 'plumber._plumber.Plumber'>

                   >>> issubclass(ClassReallyUsingAPlumbing, object)
                   True

                   >>> IPlugin1.implementedBy(ClassReallyUsingAPlumbing)
                   True
        1:     """
        1:     __pipeline__ = (Plugin1,)

``parts/coverage/plumber.__init__.cover``:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
        1: from plumber._plumber import Plumber
        1: from plumber._plumber import default
        1: from plumber._plumber import extend
        1: from plumber._plumber import plumb

``parts/coverage/plumber._plumber.cover``:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
        1: import os

           # We are aware of ``zope.interface.Interface``: if zope.interfaces is available
           # we check interfaces implemented on the plumbing plugins and will make the
           # plumbing implement them, too.
        1: try:
        1:     from zope.interface import classImplements
        1:     from zope.interface import implementedBy
        1:     ZOPE_INTERFACE_AVAILABLE = True
    >>>>>> except ImportError:
    >>>>>>     ZOPE_INTERFACE_AVAILABLE = False


        2: class PlumbingCollision(RuntimeError):
        1:     pass


        2: class default(object):
               """Provide a default value for something

               The first plugin with a default value wins the first round: its value is
               set on the plumbing as if it was declared there.

               Attributes set with the ``extend`` decorator overrule ``default``
               attributes (see ``extend`` decorator).
        1:     """
        1:     def __init__(self, attr):
        5:         self.attr = attr


        2: class extend(object):
               """Declare an attribute on the plumning as if it was defined on it.

               Attribute set with the ``extend`` decorator overrule ``default``
               attributes. Two ``extend`` attributes in a chain raise a PlumbingCollision.
        1:     """
        1:     def __init__(self, attr):
        9:         self.attr = attr


        2: class plumb(classmethod):
               """Mark a method to be used in a plumbing chain.

               The signature of the method is:
               ``def foo(plb, _next, self, *args, **kw)``

               A plumbing method is a classmethod bound to the plugin class defining it
               (``plb``), as second argument it receives the next plumbing method
               (``_next``) and the third argument (``self``) is a plumbing instance, that
               for normal methods would be the first argument.

               In order to plumb a method there needs to be a non-plumbing method behind
               it provided by: a plumbing plugin via ``extend`` or ``default`` later in
               the pipeline, the class itself or one of its base classes.
        1:     """

        1: def merge_doc(first, *args):
       39:     if first.__doc__ is None:
       30:         return None
        9:     if not args:
        4:         return first.__doc__
        5:     return os.linesep.join((first.__doc__, merge_doc(*args)))


        1: def entrance(name, pipe):
               """Create an entrance to a pipeline.

               recursively:
               - pop first method from pipeline
               - create entrance to the rest of the pipe as _next
               - wrap method passing it _next and return it, if not last method
               - return last method as is, if last method
               """
               # If only one element is left in the pipe, it is a normal method that does
               # not expect a ``_next`` parameter.
       22:     if len(pipe) is 1:
       12:         return pipe[0]

               # XXX: traceback supplement for pdb, probably more than just name is needed

       10:     plumbing_method = pipe.pop(0)
       10:     _next = entrance(name, pipe)
       10:     def _entrance(self, *args, **kw):
       11:         return plumbing_method(_next, self, *args, **kw)
       10:     _entrance.__doc__ = merge_doc(_next, plumbing_method)
       10:     return _entrance


        2: class CLOSED(object):
               """used for marking a pipeline as closed
        1:     """


        2: class Plumber(type):
               """Metaclass for plumbing creation

               First the normal new-style metaclass ``type()`` is called to construct the
               class with ``name``, ``bases``, ``dct``.

               Then, if the class declares a ``__pipeline__`` attribute, the plumber
               will create a plumbing system accordingly. Attributes declared with
               ``default``, ``extend`` and ``plumb`` will be used in the plumbing.
        1:     """
        1:     def __init__(cls, name, bases, dct):
       26:         super(Plumber, cls).__init__(name, bases, dct)
                   # The metaclass is inherited.
                   # The plumber will only get active if the class it produces defines a
                   # __pipeline__.
       26:         if cls.__dict__.get('__pipeline__') is None:
        2:             return

                   # generate docstrings from all plugin classes
       24:         cls.__doc__ = merge_doc(cls, *reversed(cls.__pipeline__))

                   # Follow ``default``, ``extend`` and ``plumb`` declarations.
       24:         pipelines = {}
       24:         defaulted = {}
       61:         for plugin in cls.__pipeline__:

      280:             for name, decor in plugin.__dict__.items():
      243:                 if isinstance(decor, extend):
       13:                     if name in cls.__dict__ \
        6:                       and name not in defaulted:
                                   # XXX: provide more info what is colliding
        3:                         raise PlumbingCollision(name)
                               # just copy the attribute that was passed to the extend
                               # decorator and mark the pipeline as closed, i.e. adding
                               # further methods to it, will raise an error.
       10:                     setattr(cls, name, decor.attr)
       10:                     defaulted.pop(name, None)
       10:                     pipe = pipelines.setdefault(name, [])
       10:                     pipe.append(CLOSED)
      230:                 elif isinstance(decor, default):
       14:                     if not name in cls.__dict__:
        7:                         setattr(cls, name, decor.attr)
        7:                         defaulted[name] = None
      216:                 elif isinstance(decor, plumb):
       14:                     pipe = pipelines.setdefault(name, [])
       14:                     if pipe and pipe[-1] is CLOSED:
        2:                         raise PlumbingCollision(name)
       12:                     if name in defaulted:
        1:                         raise PlumbingCollision(name)
                               # plumbing methods are class methods bound to the plumbing
                               # plugin class, ``getattr`` on the class in combination
                               # with being a classmethod, does this for us.
       11:                     pipe.append(getattr(plugin, name))

                       # If zope.interface is available (see import at the beginning of
                       # file), we check the plugins for implemented interfaces and make
                       # the new class implement these, too.
       37:             if ZOPE_INTERFACE_AVAILABLE:
       37:                 ifaces = implementedBy(plugin)
       37:                 if ifaces is not None:
       37:                     classImplements(cls, *list(ifaces))

       30:         for name, pipe in pipelines.items():
                       # Remove CLOSED pipe marker.
       13:             if pipe[-1] is CLOSED:
        6:                 del pipe[-1]

                       # Retrieve end point from class, from what happened above it is
                       # found with priorities:
                       # 1. a plumbing plugin declared it with ``extend``
                       # 2. the plumbing class itself declared it
                       # 3. a plumbing plugin provided a ``default`` value
                       # 4. a base class provides the attribute
       13:             end_point = getattr(cls, name)
       12:             pipe.append(end_point)

                       # Finally ``entrance`` will plumb the methods together and return
                       # an entrance function, that is set on the plumbing class be and
                       # will result in a normal bound method when being retrieved by
                       # getattr().
       12:             setattr(cls, name, entrance(name, pipe))

``parts/coverage/plumber.tests.cover``:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Contributors
------------

- Florian Friesdorf <flo@chaoflow.net>
- Robert Niederreiter <rnix@squarewave.at>
- Attila Oláh
- thanks to WSGI for the concept
- thanks to #python for trying to block stupid ideas


Changes
-------

- plb instead of cls [chaoflow, rnix 2011-01-19
- default, extend, plumb [chaoflow, rnix 2011-01-19]
- initial [chaoflow, 2011-01-04]


TODO
----

- traceback should show in which plumbing class we are, not something inside
  the plumber. yafowil is doing it. jensens: would you be so kind.
- verify behaviour with pickling
- verify behaviour with ZODB persistence
