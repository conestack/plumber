
.. contents::
    :backlinks: entry
    :depth: 2

Getting Started
===============

Plumber is a package to create classes in a declarative way. A Plumbing
consists of a ``plumbing class`` and ``parts`` providing additional behavior
on it.

A plumbing is created by setting the metaclass ``plumber`` on plumbing class
and defining the plumbing parts::

    >>> from plumber import plumber
    >>> from plumber import Part
    
    >>> class Part1(Part): pass
    >>> class Part2(Part): pass
    
    >>> class SomePlumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2

The ``plumber`` metaclass adds the functionalities defined by ``Part1`` and 
``Part2`` to ``SomePlumbing`` class.

There are three functionalities which could be defined by parts

- provide ``defaults`` on plumbing classes.
- ``extend`` plumbing classes.
- build ``pipelines`` for ``endpoints`` of a plumbing class with ``plumb``.


Endpoints
---------

Endpoints are the functions, attributes and properties available on the
plumbing class after plumber has done its work.

This endpoints could be defined either by parts using the ``default`` or
``extend`` decorator, or by the plumbing class itself.


Defining defaults
-----------------

The ``default`` decorator is used for providing functions, properties and
attribues on the plumbing class which could be overwritten either by another
part, the bases of the plumbing class or by the plumbing class itself.

Example::
    
    >>> from plumber import plumber
    >>> from plumber import Part
    >>> from plumber import default
    
    >>> class Part1(Part):
    ...     x = default(0)
    ...     y = default(0)
    ...     z = default(1)
    
    >>> class Part2(Part):
    ...     x = default(0)
    ...     y = default(0)
    ...     z = default(0)
    ...     w = default(1)
    
    >>> class Base(object):
    ...     x = 0
    ...     y = 1
    
    >>> class PlumbingClass(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...     x = 1

resolution matrix for ``default``::
    
    +---------------+-----+-----+-----+-----+
    |               |        ENDPOINT       |
    +---------------+-----+-----+-----+-----+
    | PlumbingClass | (x) |     |     |     |
    +---------------+-----+-----+-----+-----+
    | Base          |  x  | (y) |     |     |
    +---------------+-----+-----+-----+-----+
    | Part1         |  x  |  y  | (z) |     |
    +---------------+-----+-----+-----+-----+
    | Part2         |  x  |  y  |  z  | (w) |
    +---------------+-----+-----+-----+-----+

    >>> plumbing = PlumbingClass()
    >>> plumbing.x
    1
    >>> plumbing.y
    1
    >>> plumbing.z
    1
    >>> plumbing.w
    1

Defining extensions
-------------------

The ``extend`` decorator is used to explicitly define functions, properties and
attribues as endpoints for a plumbing which are immutable.

They overwrite existing functions, properties and attribues defined by
``default`` decorator.

They must not be overwritten by another part, this raises an error.

Use ``extend`` decorator if you know that a function must not be overwritten
by anything else, like storage related stuff, et cetera.

Example::

    >>> from plumber import plumber
    >>> from plumber import Part
    >>> from plumber import extend
    
    >>> class Part1(Part):
    ...     y = extend(1)
    
    >>> class Part2(Part):
    ...     z = extend(1)
    
    >>> class Part3(Part):
    ...     w = extend(1)
    
    >>> class Base(object):
    ...     x = 0
    ...     y = 0
    ...     z = 0
    ...     w = 0
    ...     v = 1   
    
    >>> class PlumbingClass(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2, Part3
    ...     x = 1

Resolution matrix for ``extend``::
    
    +---------------+-----------------------------+
    |               |          ENDPOINT           |
    +---------------+-----+-----+-----+-----+-----+
    | PlumbingClass | (X) |     |     |     |     |
    +---------------+-----+-----+-----+-----+-----+
    | Part1         |     | (y) |     |     |     |
    +---------------+-----+-----+-----+-----+-----+
    | Part2         |     |     | (z) |     |     |
    +---------------+-----+-----+-----+-----+-----+
    | Part3         |     |     |     | (w) |     |
    +---------------+-----+-----+-----+-----+-----+
    | Base          |  x  |  y  |  z  |  w  | (v) |
    +---------------+-----+-----+-----+-----+-----+
    
    >>> plumbing = PlumbingClass()
    >>> plumbing.x
    1
    >>> plumbing.y
    1
    >>> plumbing.z
    1
    >>> plumbing.w
    1
    >>> plumbing.v
    1


Defining Pipelines
------------------

Plumber can be used to build pipelines for ``endpoints``. Pipelines can be
defined for functions only (atm).

To define pipelines, use the ``plumb`` decorator in your parts, i.e.::
    
    >> # pseudo code
    >> @plumb
    >> def __getitem__(_next, self, key):
    ..     ...
    ..     before next
    ..     ...
    ..     ret = _next(self, key)
    ..     ...
    ..     after next
    ..     ...
    ..     return ret

Pipelines are build after endpoints are set, and are built in order parts are
defined on ``__plumbing__`` attribute of the plumbing class.

Example::
    
    >>> from plumber import plumber
    >>> from plumber import Part
    >>> from plumber import plumb
    
    >>> class Part1(Part):
    ...     @plumb
    ...     def x(_next, self):
    ...         print 'Part1.x begin'
    ...         _next(self)
    ...         print 'Part1.x end'
    ...     @plumb
    ...     def y(_next, self):
    ...         print 'Part1.y begin'
    ...         _next(self)
    ...         print 'Part1.y end'
    
    >>> class Part2(Part):
    ...     @plumb
    ...     def y(_next, self):
    ...         print 'Part2.y begin'
    ...         _next(self)
    ...         print 'Part2.y end'
    
    >>> class Part3(Part):
    ...     @plumb
    ...     def z(_next, self):
    ...         print 'Part3.z begin'
    ...         _next(self)
    ...         print 'Part3.z end'
    
    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2, Part3
    ...     def x(self):
    ...         print 'x endpoint'
    ...     def y(self):
    ...         print 'y endpoint'
    ...     def z(self):
    ...         print 'z endpoint'

Resolution matrix for ``plumb``::
    
    +---+-------+-------+-------+----------+
    |   | Part1 | Part2 | Part3 | ENDPOINT |
    +---+-------+-------+-------+----------+
    |   |    ----------------------->      |
    | E |   x   |       |       |    x     |
    | N |    <-----------------------      |
    + T +-------+-------+-------+----------+
    | R |    ------> --------------->      |
    | A |   y   |   y   |       |    y     |
    | N |    <------ <---------------      |
    + C +-------+-------+-------+----------+
    | E |       |       |    ------->      |
    |   |       |       |   z   |    z     |
    |   |       |       |    <-------      |
    +---+-------+-------+-------+----------+
    
    >>> plumbing = PlumbingClass()
    >>> plumbing.x()
    Part1.x begin
    x endpoint
    Part1.x end
    
    >>> plumbing.y()
    Part1.y begin
    Part2.y begin
    y endpoint
    Part2.y end
    Part1.y end
    
    >>> plumbing.z()
    Part3.z begin
    z endpoint
    Part3.z end


Plumbing chains and usual subclassing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A class that will serve as normal base class for our plumbing::

    >>> class Base(object):
    ...     def foo(self):
    ...         print "Base.foo"

Two parts for the plumbing: the ``plumb`` decorator makes the methods part of
the plumbing, they are classmethods of the part declaring them ``prt``, via
``_next`` they call the next method and ``self`` is an instance of the
plumbing::

    >>> class Part1(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         print "Part1.foo start"
    ...         _next(self)
    ...         print "Part1.foo stop"

    >>> class Part2(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         print "Part2.foo start"
    ...         _next(self)
    ...         print "Part2.foo stop"

.. attention:: ``self`` is not an instance of the part class, but an
  instance of plumbing class. The system is designed so the code you write in
  plumbing methods looks as similar as possible to the code you would write
  directly on the class.


A plumbing based on ``Base`` and using the parts ``Part1`` and ``Part2``::

    >>> class PlumbingClass(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...
    ...     def foo(self):
    ...         print "PlumbingClass.foo start"
    ...         super(PlumbingClass, self).foo()
    ...         print "PlumbingClass.foo stop"

Methods provided by the parts sit in front of methods declared by the class
and its base classes::

    >>> plumbing = PlumbingClass()
    >>> plumbing.foo()
    Part1.foo start
    Part2.foo start
    PlumbingClass.foo start
    Base.foo
    PlumbingClass.foo stop
    Part2.foo stop
    Part1.foo stop

The parts are not in the class' method resolution order::

    >>> PlumbingClass.__mro__
    (<class 'PlumbingClass'>,
     <class 'Base'>,
     <type 'object'>)

    >>> issubclass(PlumbingClass, Base)
    True
    >>> issubclass(PlumbingClass, Part1)
    False
    >>> issubclass(PlumbingClass, Part2)
    False

The plumbing can be subclassed like a normal class::

    >>> class SubOfPlumbingClass(PlumbingClass):
    ...     def foo(self):
    ...         print "SubOfPlumbingClass.foo start"
    ...         super(SubOfPlumbingClass, self).foo()
    ...         print "SubOfPlumbingClass.foo stop"

    >>> subofplumbing = SubOfPlumbingClass()
    >>> subofplumbing.foo()
    SubOfPlumbingClass.foo start
    Part1.foo start
    Part2.foo start
    PlumbingClass.foo start
    Base.foo
    PlumbingClass.foo stop
    Part2.foo stop
    Part1.foo stop
    SubOfPlumbingClass.foo stop

.. note:: A class inherits the ``__metaclass__`` declaration from base classes.
  The ``plumber`` metaclass is called for ``PlumbingClass`` **and**
  ``SubOfPlumbingClass``. However, it will only get active for a class that
  declares a ``__plumbing__`` itself and otherwise just calls ``type``, the
  default metaclass for new-style classes.


Passing parameters to methods in a plumbing chain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parameters to plumbing methods are passed in via keyword arguments - there is
no sane way to do this via positional arguments (see section Default
attributes for application to ``__init__`` plumbing)::

    >>> class Part1(Part):
    ...     @plumb
    ...     def foo(_next, self, *args, **kw):
    ...         print "Part1.foo: args=%s" % (args,)
    ...         print "Part1.foo: kw=%s" % (kw,)
    ...         self.p1 = kw.pop('p1', None)
    ...         _next(self, *args, **kw)

    >>> class Part2(Part):
    ...     @plumb
    ...     def foo(_next, self, *args, **kw):
    ...         print "Part2.foo: args=%s" % (args,)
    ...         print "Part2.foo: kw=%s" % (kw,)
    ...         self.p2 = kw.pop('p2', None)
    ...         _next(self, *args, **kw)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...     def foo(self, *args, **kw):
    ...         print "PlumbingClass.foo: args=%s" % (args,)
    ...         print "PlumbingClass.foo: kw=%s" % (kw,)

The plumbing parts pick what they need, the remainging keywords and all
positional arguments are just passed through to the plumbing class::

    >>> foo = PlumbingClass()
    >>> foo.foo('blub', p1='p1', p2='p2', plumbing='plumbing')
    Part1.foo: args=('blub',)
    Part1.foo: kw={'p2': 'p2', 'plumbing': 'plumbing', 'p1': 'p1'}
    Part2.foo: args=('blub',)
    Part2.foo: kw={'p2': 'p2', 'plumbing': 'plumbing'}
    PlumbingClass.foo: args=('blub',)
    PlumbingClass.foo: kw={'plumbing': 'plumbing'}


End-points for plumbing chains
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Plumbing chains need a normal method to serve as end-point::

    >>> class Part1(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         pass

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    Traceback (most recent call last):
      ...
    AttributeError: type object 'PlumbingClass' has no attribute 'foo'

It is looked up on the class with ``getattr``, after the plumbing pipeline is
processed, but before it is installed on the class.

It can be provided by the plumbing class itself::

    >>> class Part1(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         print "Part1.foo start"
    ...         _next(self)
    ...         print "Part1.foo stop"

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    ...
    ...     def foo(self):
    ...         print "PlumbingClass.foo"

    >>> plumbing = PlumbingClass().foo()
    Part1.foo start
    PlumbingClass.foo
    Part1.foo stop

It can be provided by a base class of the plumbing class::

    >>> class Base(object):
    ...     def foo(self):
    ...         print "Base.foo"

    >>> class Part1(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         print "Part1.foo start"
    ...         _next(self)
    ...         print "Part1.foo stop"

    >>> class PlumbingClass(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1

    >>> plumbing = PlumbingClass().foo()
    Part1.foo start
    Base.foo
    Part1.foo stop

Further it can be provided by a plumbing part with the ``default`` or
``extend`` decorators (see Extending classes, an alternative to mixins), it
will be put on the plumbing class, before the end point it looked up and
therefore behaves exactly like the method would be declared on the class
itself.


Plumbing for property getter, setter and deleter.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Properties with named functions, non-decorated
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
    >>> class Base(object):
    ...     def get_a(self):
    ...         return self._a
    ...     def set_a(self, val):
    ...         self._a = val
    ...     def del_a(self):
    ...         del self._a
    ...     a = property(get_a, set_a, del_a)

    >>> class ClassInheritingProperty(Base):
    ...     pass

    >>> cip = ClassInheritingProperty()
    >>> hasattr(cip, '_a')
    False
    >>> cip.a = 1
    >>> cip._a
    1
    >>> cip.a
    1
    >>> del cip.a
    >>> hasattr(cip, '_a')
    False

A property is realised by a property descriptor object in the ``__dict__`` of
the class defining it::

    >>> Base.__dict__['a']
    <property object at 0x...>

    >>> Base.__dict__['a'].fset(cip, 2)
    >>> Base.__dict__['a'].fget(cip)
    2
    >>> Base.__dict__['a'].fdel(cip)

From now on we skip the deleter.

If you want to change an aspect of a property, you need to redefine it, except
if it uses lambda abstraction (see below). As the function used as getter is
also in the Base class' ``__dict__`` we can use it, saving some overhead::

    >>> class ClassOverridingProperty(Base):
    ...     def get_a(self):
    ...         return 2 * super(ClassOverridingProperty, self).get_a()
    ...     a = property(get_a, Base.set_a)

    >>> cop = ClassOverridingProperty()
    >>> cop.a = 5
    >>> cop.a
    10

Properties with decorated or unnamed getter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In case the property is realised by a decorated function or a single lambda -
both cases result in a read-only property - the function used as getter is not
anymore in the class' ``__dict__``::

    >>> class PropWithoutDictFuncBase(object):
    ...     @property
    ...     def a(self):
    ...         return self._a
    ...     b = property(lambda self: self._b)

    >>> class PropWithoutDictFunc(PropWithoutDictFuncBase):
    ...     @property
    ...     def a(self):
    ...         return 2 * super(PropWithoutDictFunc, self).a
    ...     b = property(lambda self: 3 * super(PropWithoutDictFunc, self).b)

    >>> pwdf = PropWithoutDictFunc()
    >>> pwdf._a = 2
    >>> pwdf._b = 2
    >>> pwdf.a
    4
    >>> pwdf.b
    6

Lambda abstraction
^^^^^^^^^^^^^^^^^^
If a base class uses lambdas to add a layer of abstraction it is easier to
override a single aspect, but adds another call (see Benchmarking below)::

    >>> class LambdaBase(object):
    ...     def get_a(self):
    ...         return self._a
    ...     def set_a(self, val):
    ...         self._a = val
    ...     a = property(
    ...             lambda self: self.get_a(),
    ...             lambda self, val: self.set_a(val),
    ...             )

    >>> class ClassInheritingLambdaProperty(LambdaBase):
    ...     def get_a(self):
    ...         return 3 * super(ClassInheritingLambdaProperty, self).get_a()

    >>> cilp = ClassInheritingLambdaProperty()
    >>> cilp.a = 2
    >>> cilp.a
    6

Plumbing of a property that uses lambda abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Aspects of a property that uses lambda abstraction are easily plumbed::

    >>> class LambdaBase(object):
    ...     def get_a(self):
    ...         return self._a
    ...     def set_a(self, val):
    ...         self._a = val
    ...     a = property(
    ...             lambda self: self.get_a(),
    ...             lambda self, val: self.set_a(val),
    ...             )

    >>> class PropertyPlumbing(Part):
    ...     @plumb
    ...     def get_a(_next, self):
    ...         return 4 * _next(self)

    >>> class PlumbedLambdaProperty(LambdaBase):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = PropertyPlumbing

    >>> plp = PlumbedLambdaProperty()
    >>> plp.a = 4
    >>> plp.a
    16

Plumbing properties that do not use lambda abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
#XXX#    >>> def set_a(self, val):
#XXX#    ...     self._a = val
#XXX#
#XXX#    >>> def del_a(self):
#XXX#    ...     del self._a
#XXX#
#XXX#    >>> class Base(object):
#XXX#    ...     a = property(lambda self: self._a, set_a, del_a)
#XXX#
#XXX#    >>> class Notify(Part):
#XXX#    ...     def get_a(_next, self):
#XXX#    ...         print "Getting a"
#XXX#    ...         return _next(self)
#XXX#    ...     def set_a(_next, self, val):
#XXX#    ...         print "Setting a"
#XXX#    ...         _next(self, val)
#XXX#    ...     def del_a(_next, self):
#XXX#    ...         print "Deleting a"
#XXX#    ...         _next(self)
#XXX#    ...     a = plumb(property(get_a, set_a, del_a))
#XXX#
#XXX#    >>> class Multiply(Part):
#XXX#    ...     def get_a(_next, self):
#XXX#    ...         return _next(self) * 2
#XXX#    ...     def set_a(_next, self, val):
#XXX#    ...         _next(self, val)
#XXX#    ...     def del_a(_next, self):
#XXX#    ...         _next(self)
#XXX#    ...     a = plumb(property(get_a, set_a, del_a))
#XXX#
#XXX#    >>> class Plumbing(Base):
#XXX#    ...     __metaclass__ = plumber
#XXX#    ...     __plumbing__ = Notify, Multiply
#XXX#
#XXX#    >>> plumbing = Plumbing()
#XXX#    >>> hasattr(plumbing, '_a')
#XXX#    False
#XXX#    >>> plumbing.a = 8
#XXX#    Setting a
#XXX#    >>> plumbing.a
#XXX#    Getting a
#XXX#    16
#XXX#    >>> hasattr(plumbing, '_a')
#XXX#    True
#XXX#    >>> del plumbing.a
#XXX#    Deleting a
#XXX#    >>> hasattr(plumbing, '_a')
#XXX#    False
#XXX#
#XXX#A base class has a readonly property, a plumbing property plumbs in::
#XXX#
#XXX#    >>> class Base(object):
#XXX#    ...     _foo = 5
#XXX#    ...     @property
#XXX#    ...     def foo(self):
#XXX#    ...         return self._foo
#XXX#
#XXX#    >>> class Part(Part):
#XXX#    ...     @plumb
#XXX#    ...     @property
#XXX#    ...     def foo(_next, self):
#XXX#    ...         return 3 * _next(self)
#XXX#
#XXX#    >>> class Plumbing(Base):
#XXX#    ...     __metaclass__ = plumber
#XXX#    ...     __plumbing__ = Part
#XXX#
#XXX#    >>> plumbing = Plumbing()
#XXX#    >>> plumbing.foo
#XXX#    15
#XXX#    >>> plumbing.foo = 10
#XXX#    Traceback (most recent call last):
#XXX#      ...
#XXX#    AttributeError: can't set attribute
#XXX#
#XXX#Extend the attribute to make it writable::
#XXX#
#XXX#    >>> class Part(Part):
#XXX#    ...     @plumb
#XXX#    ...     @property
#XXX#    ...     def foo(_next, self):
#XXX#    ...         return 3 * _next(self)
#XXX#    ...     @foo.setter
#XXX#    ...     def foo(_next, self, val):
#XXX#    ...         _next(self, val)
#XXX#
#XXX#    >>> class Plumbing(Base):
#XXX#    ...     __metaclass__ = plumber
#XXX#    ...     __plumbing__ = Part
#XXX#
#XXX#    >>> plumbing = Plumbing()
#XXX#    >>> plumbing.foo
#XXX#    15
#XXX#
#XXX##    >>> plumbing.foo = 10
#XXX##    >>> plumbing.foo
#XXX##    30


Extending classes through plumbing, an alternative to mixins
------------------------------------------------------------

Why? It's more fun.

.. contents::
    :backlinks: entry
    :local:

Extending a class
~~~~~~~~~~~~~~~~~
A part can put arbitrary attributes onto a class as if they were declared on it::

    >>> class Part1(Part):
    ...     foo = extend(False)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1

The attribute is defined on the class, setting it on an instance will store the
value in the instance's ``__dict__``::

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
is raised::

    >>> class Part1(Part):
    ...     foo = extend(False)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    ...     foo = False
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        Plumbing class
      with:
        <extend 'foo' of <class 'Part1'> payload=False>

XXX: increase verbosity of exception

Also, if two parts try to extend an attribute with the same name, an
exception is raised. The situation before processing the second part is
exactly as if the method was declared on the class itself::

not a collision, both extend want the same::

    >>> class Part1(Part):
    ...     foo = extend(False)

    >>> class Part2(Part):
    ...     foo = extend(False)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2

a collision::

    >>> class Part1(Part):
    ...     foo = extend(False)

    >>> class Part2(Part):
    ...     foo = extend(True)

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        <extend 'foo' of <class 'Part1'> payload=False>
      with:
        <extend 'foo' of <class 'Part2'> payload=True>

Extending a method needed by a part earlier in the chain works::

    >>> class Part1(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         print "Part1.foo start"
    ...         _next(self)
    ...         print "Part1.foo stop"

    >>> class Part2(Part):
    ...     @extend
    ...     def foo(self):
    ...         print "Part2.foo"

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2

    >>> PlumbingClass().foo()
    Part1.foo start
    Part2.foo
    Part1.foo stop

Extended methods close pipelines, adding a plumbing method afterwards raises an
exception::

    >>> class Part1(Part):
    ...     @extend
    ...     def foo(self):
    ...         pass

    >>> class Part2(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         pass

    >>> class Part3(Part):
    ...     @extend
    ...     def foo(_next, self):
    ...         pass

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2, Part3
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        <extend 'foo' of <class 'Part1'> payload=<function foo at 0x...>>
      with:
        <extend 'foo' of <class 'Part3'> payload=<function foo at 0x...>>

It is possible to make super calls from within the method added by the part::

    >>> class Base(object):
    ...     def foo(self):
    ...         print "Base.foo"

    >>> class Part1(Part):
    ...     @extend
    ...     def foo(self):
    ...         print "Part1.foo start"
    ...         super(self.__class__, self).foo()
    ...         print "Part1.foo stop"

    >>> class PlumbingClass(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1

    >>> plumbing = PlumbingClass()
    >>> plumbing.foo()
    Part1.foo start
    Base.foo
    Part1.foo stop

Extension is used if a part relies on a specific attribute value, most common
the case with functions. If a part provides a setting it uses a default
value (see next section).

Default attributes
~~~~~~~~~~~~~~~~~~
Parts that use parameters, provide defaults that are overridable. Further it
should enable setting these parameters through a ``__init__`` plumbing method::

    >>> class Part1(Part):
    ...     foo = default(False)
    ...     @plumb
    ...     def __init__(_next, self, *args, **kw):
    ...         if 'foo' in kw:
    ...             self.foo = kw.pop('foo')
    ...         _next(self, *args, **kw)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    ...     def __init__(self, bar=None):
    ...         self.bar = bar

The default value is set in the class' ``__dict__``::

    >>> Plumbing.foo
    False
    >>> plumbing = Plumbing()
    >>> plumbing.foo
    False
    >>> 'foo' in plumbing.__dict__
    False

Setting the value on the instance is persistent and the class' value is
untouched::

    >>> plumbing.foo = True
    >>> plumbing.foo
    True
    >>> Plumbing.foo
    False

Values can be provided to ``__init__``::

    >>> plumbing = Plumbing(bar=42, foo=True)
    >>> plumbing.foo
    True
    >>> Plumbing.foo
    False
    >>> plumbing.bar
    42

The innermost part prodiving a default value is taken, other defaults are
ignored::

    >>> class One(Part):
    ...     foo = default(1)

    >>> class Two(Part):
    ...     foo = default(2)
    ...     bar = default(foo)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = One, Two

    >>> Plumbing.foo
    1
    >>> Plumbing.bar
    2

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Two, One

    >>> Plumbing.foo
    2

An attribute declared on the class overwrites ``default`` attributes::

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = One, Two
    ...     foo = None

    >>> print Plumbing.foo
    None

``Extend`` overrules ``default``::

#XXX#    >>> class Default(Part):
#XXX#    ...     foo = default('default')
#XXX#
#XXX#    >>> class Extend(Part):
#XXX#    ...     foo = extend('extend')
#XXX#
#XXX#    >>> class Plumbing(object):
#XXX#    ...     __metaclass__ = plumber
#XXX#    ...     __plumbing__ = Extend, Default
#XXX#
#XXX#    >>> Plumbing.foo
#XXX#    'extend'
#XXX#
#XXX#    >>> class Plumbing(object):
#XXX#    ...     __metaclass__ = plumber
#XXX#    ...     __plumbing__ = Default, Extend
#XXX#
#XXX#    >>> Plumbing.foo
#XXX#    'extend'
#XXX#
#XXX#    >>> class Plumbing(object):
#XXX#    ...     __metaclass__ = plumber
#XXX#    ...     __plumbing__ = Default, Extend, Default
#XXX#
#XXX#    >>> Plumbing.foo
#XXX#    'extend'
#XXX#
#XXX#``default`` does not interfere with ``extend`` collision detection::
#XXX#
#XXX#    >>> class Plumbing(object):
#XXX#    ...     __metaclass__ = plumber
#XXX#    ...     __plumbing__ = Default, Extend, Default, Extend, Default
#XXX#    Traceback (most recent call last):
#XXX#      ...
#XXX#    PlumbingCollision:
#XXX#        <extend 'foo' of <class 'Extend'> payload=extend>
#XXX#      with:
#XXX#        <extend 'foo' of <class 'Extend'> payload=extend>
#XXX#

``plumb`` and either ``default`` or ``extend`` collide::

#    >>> class Default(Part):
#    ...     foo = default(None)
#
#    >>> class Extend(Part):
#    ...     foo = extend(None)
#
#    >>> class Plumb(Part):
#    ...     @plumb
#    ...     def foo(_next, self):
#    ...         pass
#
#    >>> class Plumbing(object):
#    ...     __metaclass__ = plumber
#    ...     __plumbing__ = Default, Plumb
#    Traceback (most recent call last):
#      ...
#    PlumbingCollision: 'foo'...
#
#    >>> class Plumbing(object):
#    ...     __metaclass__ = plumber
#    ...     __plumbing__ = Extend, Plumb
#    Traceback (most recent call last):
#      ...
#    PlumbingCollision: foo

Extend/default properties
~~~~~~~~~~~~~~~~~~~~~~~~~
The ``extend`` and ``default`` decorators are agnostic to the type of attribute
they are decorating, it works as well on properties.

    >>> class PropPart(Part):
    ...     @extend
    ...     @property
    ...     def foo(self):
    ...         return 5
    ...
    ...     @default
    ...     @property
    ...     def bar(self):
    ...         return 17

    >>> class PlumbingClass(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = PropPart

    >>> plumbing = PlumbingClass()
    >>> plumbing.foo
    5
    >>> plumbing.bar
    17


Plumbing docstrings
-------------------

The plumbing's docstring is generated from the ``__doc__`` declared on the
plumbing class followed by part classes' ``__doc__`` in reverse order,
``None`` docstrings are skipped::

    >>> class P1(Part):
    ...     """P1
    ...     """

    >>> class P2(Part):
    ...     pass

    >>> class P3(Part):
    ...     """P3
    ...     """

    >>> class Plumbing(object):
    ...     """Plumbing
    ...     """
    ...     __metaclass__ = plumber
    ...     __plumbing__ = P1, P2, P3

XXX: protect whitespace from testrunner normalization

::

    >>> print Plumbing.__doc__
    P1
    <BLANKLINE>
    P3
    <BLANKLINE>
    Plumbing
    <BLANKLINE>

If all are None the docstring is also None::

    >>> class P1(Part):
    ...     pass

    >>> class P2(Part):
    ...     pass

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = P1, P2

    >>> print Plumbing.__doc__
    None

Docstrings for the entrance methods are generated alike::

    >>> class P1(Part):
    ...     @plumb
    ...     def foo():
    ...         """P1.foo
    ...         """

    >>> class P2(Part):
    ...     @plumb
    ...     def foo():
    ...         pass

    >>> class P3(Part):
    ...     @plumb
    ...     def foo():
    ...         """P3.foo
    ...         """

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = P1, P2, P3
    ...     def foo():
    ...         """Plumbing.foo
    ...         """

XXX: protect whitespace from testrunner normalization

::

    >>> print Plumbing.foo.__doc__
    P1.foo
    <BLANKLINE>
    P3.foo
    <BLANKLINE>
    Plumbing.foo
    <BLANKLINE>


zope.interface support
----------------------

The plumber does not depend on ``zope.interface`` but is aware of it. That
means it will try to import it and if available will check plumbing classes
for implemented interfaces and will make the new class implement them, too::

    >>> from zope.interface import Interface
    >>> from zope.interface import implements

A class with an interface that will serve as base::

    >>> class IBase(Interface):
    ...     pass

    >>> class Base(object):
    ...     implements(IBase)

    >>> IBase.implementedBy(Base)
    True

Two parts with corresponding interfaces, one with a base class that also
implements an interface::

    >>> class IPart1(Interface):
    ...     pass

    >>> class Part1(Part):
    ...     blub = 1
    ...     implements(IPart1)

    >>> class IPart2Base(Interface):
    ...     pass

    >>> class Part2Base(Part):
    ...     implements(IPart2Base)

    >>> class IPart2(Interface):
    ...     pass

    >>> class Part2(Part2Base):
    ...     implements(IPart2)

    >>> IPart1.implementedBy(Part1)
    True
    >>> IPart2Base.implementedBy(Part2Base)
    True
    >>> IPart2Base.implementedBy(Part2)
    True
    >>> IPart2.implementedBy(Part2)
    True

A class based on ``Base`` using a plumbing of ``Part1`` and ``Part2`` and
implementing ``IPlumbingClass``::

    >>> class IPlumbingClass(Interface):
    ...     pass

    >>> class PlumbingClass(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...     implements(IPlumbingClass)

The directly declared and inherited interfaces are implemented::

    >>> IPlumbingClass.implementedBy(PlumbingClass)
    True
    >>> IBase.implementedBy(PlumbingClass)
    True

The interfaces implemented by the parts are also implemented::

    >>> IPart1.implementedBy(PlumbingClass)
    True
    >>> IPart2.implementedBy(PlumbingClass)
    True
    >>> IPart2Base.implementedBy(PlumbingClass)
    True

An instance of the class provides the interfaces::

    >>> plumbing = PlumbingClass()

    >>> IPlumbingClass.providedBy(plumbing)
    True
    >>> IBase.providedBy(plumbing)
    True
    >>> IPart1.providedBy(plumbing)
    True
    >>> IPart2.providedBy(plumbing)
    True
    >>> IPart2Base.providedBy(plumbing)
    True

The reasoning behind this is: the plumbing classes are behaving as close as
possible to base classes of our class, but without using subclassing.  For an
additional maybe future approach see Discussion.


Nomenclature
------------

The nomenclature is just forming and still inconsistent.

plumber
    Metaclass that creates a plumbing system according to the instructions on
    plumbing parts: ``default``, ``extend`` and ``plumb``.

plumbing (system)
    A plumbing is the result of what the plumber produces. It is built of
    methods declared on base classes, the plumbing class and plumbing parts
    according to ``default``, ``extend`` and ``plumb`` directives. Parts
    involved are listed in a class' ``__plumbing__`` attribute.

pipeline attribute
    The attribute a class uses to define the order of plumbing class to be used
    to create the plumbing.

plumbing class
    Synonymous for plumbing system, but sometimes also only the class that asks
    to be turned into a plumbing, esp. when referring to attributes declared on
    it.

(plumbing) part / part class
    A plumbing part provides attributes to be used for the plumbing through
    ``default``, ``extend`` and ``plumb`` declarations.

``default`` decorator
    Instruct the plumber to set a default value: first default wins, ``extend``
    and declaration on plumbing class takes precedence.

``extend`` decorator
    Instruct the plumber to set an attribute on the plumbing: ``extend``
    overrides ``default``, two ``extend`` collide.

``plumb`` decorator
    Instruct the plumber to make a function part of a plumbing chain and turns
    the function into a classmethod bound to the plumbing part declaring it
    with a signature of: ``def foo(_next, self, *args, **kw)``.
    ``prt`` is the part class declaring it, ``_next`` a wrapper for the next
    method in chain and ``self`` and instance of the plumbing

default attribute
    Attribute set via the ``default`` decorator.

extension attribute
    Attribute set via the ``extend`` decorator.

plumbing method
    Method declared via the ``plumb`` decoarator.

plumbing chain
    The methods of a pipeline with the same name plumbed together. The entrance
    and end-point have the signature of normal methods: ``def foo(self, *args,
    **kw)``. The plumbing chain is a series of nested closures (see ``_next``).

entrance method
    A method with a normal signature. i.e. expecting ``self`` as first
    argument, that is used to enter a plumbing chain. It is a ``_next``
    function. A method declared on the class with the same name, will be
    overwritten, but referenced in the chain as the innermost method, the
    end-point.

``_next`` function
    The ``_next`` function is used to call the next method in a chain: in case of
    a plumbing method, a wrapper of it that passes the correct next ``_next``
    as first argument and in case of an end-point, just the end-point method
    itself.

end-point (method)
    Method retrieved from the plumbing class with ``getattr()``, before setting
    the entrance method on the class. It is provided with the following
    precedence:

    1. plumbing class itself,
    2. plumbing extension attribute,
    3. plumbing default attribute,
    4. bases of the plumbing class.


Discussions
-----------

.. contents::
    :backlinks: entry
    :local:

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
``__init__`` would need a different name, eg. ``prt_``-prefix. Consequently
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
interfaces for the parts and the class that is created::

    #    >>> class IPart1Behaviour(Interface):
    #    ...     pass
    #
    #    >>> class Part1(Part):
    #    ...     implements(IPart1)
    #    ...     interfaces = (IPart1Behaviour,)
    #
    #    >>> class IPart2(Interface):
    #    ...     pass
    #
    #    >>> class Part2(Part):
    #    ...     implements(IPart2)
    #    ...     interfaces = (IPart2Behaviour,)
    #
    #    >>> IUs.implementedBy(Us)
    #    True
    #    >>> IBase.implementedBy(Us)
    #    True
    #    >>> IPart1.implementedBy(Us)
    #    False
    #    >>> IPart2.implementedBy(Us)
    #    False
    #    >>> IPart1Behaviour.implementedBy(Us)
    #    False
    #    >>> IPart2Behaviour.implementedBy(Us)
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
The plumber could replace the ``__plumbing__`` attribute with a property of the
same name. Changing the attribute during runtime would result in a plumbing
specific to the object. A plumbing cache could further be used to reduce the
number of plumbing chains in case of many dynamic plumbings. Realised eg by a
descriptor.


Test Coverage
-------------

XXX: automatic update of coverage report

Summary of the test coverage report::

    lines   cov%   module   (path)
        5   100%   plumber.__init__
      157    92%   plumber._instructions
       41   100%   plumber._part
       50   100%   plumber._plumber
       10   100%   plumber.exceptions
       18   100%   plumber.tests._globalmetaclasstest
       16   100%   plumber.tests.test_


Detailed
~~~~~~~~
XXX: Would this be sane to have here? Include coverage files as preformatted?


About
-----

Contributors
~~~~~~~~~~~~
- Florian Friesdorf <flo@chaoflow.net>
- Robert Niederreiter <rnix@squarewave.at>
- Jens W. Klein <jens@bluedynamics.com>
- Attila Oláh
- thanks to WSGI for the concept
- thanks to #python (for trying) to block stupid ideas


Changes
~~~~~~~
- stage1 in __new__, stage2 in __init__, setting of __name__ now works
  [chaoflow 2011-01-25]

- instructions recognize equal instructions
  [chaoflow 2011-01-24]

- instructions from base classes now like subclass inheritance [chaoflow 2011
  [chaoflow 2011-01-24]

- doctest order now plumbing order: P1, P2, PlumbingClass, was PlumbingClass,
  P1, P2
  [chaoflow 2011-01-24]

- merged docstring instruction into plumb
  [chaoflow 2011-01-24]

- plumber instead of Plumber
  [chaoflow 2011-01-24]

- plumbing methods are not classmethods of part anymore
  [chaoflow 2011-01-24]

- complete rewrite
  [chaoflow 2011-01-22]

- prt instead of cls
  [chaoflow, rnix 2011-01-19

- default, extend, plumb
  [chaoflow, rnix 2011-01-19]

- initial
  [chaoflow, 2011-01-04]


TODO
~~~~
- traceback should show in which plumbing class we are, not something inside
  the plumber. yafowil is doing it. jensens: would you be so kind.
- verify behaviour with pickling
- verify behaviour with ZODB persistence
- subclassing for plumbing parts
- plumbing of property getter, setter and deleter for non-lambda properties


Disclaimer
~~~~~~~~~~

TODO




Subclass gets its own stacks
----------------------------

    >>> class Part1(Part):
    ...     a = extend(1)

    >>> class Base(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1

    >>> class Sub(Base):
    ...     __plumbing__ = Part1

