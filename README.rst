Plumber
=======

XXX: Intro

Motivation
----------

Plumbing is an alternative to mixin-based extension of classes, motivated by
limitations and/or design choice of python's subclassing:

.. content::
    :local:

Control of precedence only through order of mixins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mixins are commonly used to extend classes with pre-defined behaviours: an
attribute on the first mixin overwrites attributes with the same name on all
following mixins and the base class being extended::

    >>> class Mixin1(object):
    ...     a = 1

    >>> class Mixin2(object):
    ...     a = 2
    ...     b = 2

    >>> Base = dict
    >>> class MixedClass(Mixin1, Mixin2, Base):
    ...     pass

    >>> MixedClass.a
    1
    >>> MixedClass.b
    2
    >>> MixedClass.keys
    <method 'keys' of 'dict' objects>

There is no way for a mixin later in the chain to take precedence over an
earlier one.

**Solution**: plumber provides 3 decorators to enable finer control of
precedence (``default``, ``extend``, ``finalize``).

Impossible to provide default values to fill gaps on a base class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A dictionary-like storage at least needs to provide ``__getitem__``,
``__setitem__``, ``__delitem__`` and ``__iter__``, all other methods of a
dictionary can be build upon these. A mixin that turns storages into full
dictionaries needs to be able to provide default methods, taken if the base
class does not provide a (more efficient) implementation.

**Solution**: plumber provides the ``default`` decorator to enable such
defaults.

Endpoints for ``super``-chains are checked during runtime
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
It is possible to build a chain of methods using ``super``: ``Mixin1`` turns
the key lowercase before passing it on, ``Mixin2`` multiplies the result by 2
before returning it and both are chatty about start/stop::

    >>> class Mixin1(object):
    ...     def __getitem__(self, key):
    ...         print "Mixin1 start"
    ...         key = key.lower()
    ...         ret = super(Mixin1, self).__getitem__(key)
    ...         print "Mixin1 stop"
    ...         return ret

    >>> class Mixin2(object):
    ...     def __getitem__(self, key):
    ...         print "Mixin2 start"
    ...         ret = super(Mixin2, self).__getitem__(key)
    ...         ret = 2 * ret
    ...         print "Mixin2 stop"
    ...         return ret

    >>> Base = dict
    >>> class MixedClass(Mixin1, Mixin2, Base):
    ...     pass

    >>> mc = MixedClass()
    >>> mc['abc'] = 6
    >>> mc['ABC']
    Mixin1 start
    Mixin2 start
    Mixin2 stop
    Mixin1 stop
    12

``dict.__getitem__`` forms the endpoint of the chain as it returns a value
without delegating to a method later in the chain (using ``super``). If there
is no endpoint an ``AttributeError`` is raised during runtime.

The chain is not verified during class creation.

**Solution**: Plumber provides the ``plumb`` decorator to build similar chains
using nested closures. These are create and verified during class creation.

No conditional ``super``-chains
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A mixin with subclassing needs to fit exactly the base class, there is no way
to conditionally hook into method calls depending on whether the base class
provides a method.

**Solution**: Plumber provides the ``plumbifexists`` decorator that behaves
like ``plumb``, if there is an endpoint available.

Docstrings are not accumulated
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A class' docstring that uses mixins is not build from the docstrings of the
mixins.

**Solution**: Plumber enables plumbing of docstrings using a special marker
``.. plbnext::``, which is replaced with the docstring of the next "mixin"
Without the marker, docstrings are concatenated.


The plumbing system
-------------------

The ``plumber`` metaclass creates plumbing classes according to instructions
found on plumbing parts.

XXX:

Plumbing parts
^^^^^^^^^^^^^^
Plumbing parts correspond to mixins, but are more powerful and flexible. A
plumbing part needs to inherit from ``plumber.Part`` and declares attributes
with instructions on how to use them, here by example of the ``default``
instruction (see Plumbing Instructions for more)::

    >>> from plumber import Part
    >>> from plumber import default

    >>> class Part1(Part):
    ...     a = default(True)
    ...
    ...     @default
    ...     def foo(self):
    ...         return 42

The instructions are given as part of assignments (``a = default(None)``) or as
decorators (``@default``).

A plumbing declaration defines the ``plumber`` as metaclass and one or more
plumbing parts to be processed from left to right. Further it may declare
attributes like every normal class, they will be treated as implicit
``finalize`` instructions (see Stage 1: Extension)::

    >>> from plumber import plumber

    >>> class Part2(Part):
    ...     pass

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...
    ...     def bar(self):
    ...         return 17

The result is a plumbing class created according to the plumbing declaration::

    >>> Plumbing.a
    True
    >>> Plumbing().foo()
    42
    >>> Plumbing().bar()
    17

Plumbing instructions
^^^^^^^^^^^^^^^^^^^^^
Plumbing instructions are grouped into two stages:

1. extension via ``default``, ``extend`` and ``finalize``
2. creation of pipelines via ``plumb`` and ``plumbifexists``

Plumbing pipelines correspond to ``super``-chains, they need endpoints, which
are created during the first stage.

Within a stage, instructions are grouped by attribute name in part order.

Apart from instructions on plumbing parts, declarations on the plumbing class
and its base classes are taken into account.

Stage 1: Extension
~~~~~~~~~~~~~~~~~~
The extension stage creates endpoints for the pipelines created in stage 2. If
no pipeline uses the endpoint, it will just live on as a normal attribute in
the plumbind class' dictionary.

The extension decorators:

``finalize``
    ``finalize`` is the strongest extension instruction. It will override
    declarations on base classes and all other extension instructions
    (``extend`` and ``default``). Attributes declared as part of the plumbing
    declaration are implicit ``finalize`` declarations. Two ``finalize`` for
    one attribute name will collide and raise a ``PlumbingCollision`` during
    class creation.

    +-------+-------+----------+-------+-----------+
    | Part1 | Part2 | Plumbing | Base  |    ok?    |
    +=======+=======+==========+======-+===========|
    |       |       |          | **x** |           |
    +-------+-------+----------+-------+-----------+
    |       |       |  **x**   |   ?   |           |
    +-------+-------+----------+-------+-----------+
    |       | **f** |          |   ?   |           |
    +-------+-------+----------+-------+-----------+
    | **f** |       |          |   ?   |           |
    +-------+-------+----------+-------+-----------+
    |       |   f   |    x     |   ?   | collision |
    +-------+-------+----------+-------+-----------+
    |   f   |   f   |    x     |   ?   | collision |
    +-------+-------+----------+-------+-----------+
    |   f   |   f   |          |   ?   | collision |
    +-------+-------+----------+-------+-----------+

``extend``
    ``extend`` is weaker than ``finalize`` and overrides declarations on base
    classes and ``default`` declarations. Two ``extend`` instructions for the
    same attribute name do not collide, instead the first one will be used.

    +-------+-------+----------+-------+
    | Part1 | Part2 | Plumbing | Base  |
    +=======+=======+==========+=======+
    |   e   |   e   |  **x**   |   ?   |
    +-------+-------+----------+-------+
    |       | **e** |          |   ?   |
    +-------+-------+----------+-------+
    | **e** |   e   |          |   ?   |
    +-------+-------+----------+-------+

``default``
    ``default`` is the weakest extension instruction. It will not even override
    declarations of base classes. The first default takes precendence over
    later defaults.

    +-------+-------+----------+-------+
    | Part1 | Part2 | Plumbing | Base  |
    +=======+=======+==========+=======+
    |       |   d   |          | **x** |
    +-------+-------+----------+-------+
    |       |   d   |  **x**   |   ?   |
    +-------+-------+----------+-------+
    |       | **d** |          |       |
    +-------+-------+----------+-------+
    | **d** |   d   |          |       |
    +-------+-------+----------+-------+

``finalize`` wins over ``extend``:

    +-------+-------+----------+------+
    | Part1 | Part2 | Plumbing | Base |
    +=======+=======+==========+======+
    |   e   | **f** |          |   ?  |
    +-------+-------+----------+------+
    | **f** |   e   |          |   ?  |
    +-------+-------+----------+------+

``extend`` wins over ``default``, but loses against plumbing class declaration:

    +-------+-------+----------+------+
    | Part1 | Part2 | Plumbing | Base |
    +=======+=======+==========+======+
    |   d   |   e   |  **x**   |   ?  |
    +-------+-------+----------+------+
    |   d   | **e** |          |   ?  |
    +-------+-------+----------+------+
    | **e** |   d   |          |   ?  |
    +-------+-------+----------+------+

``finalize`` wins over ``default``:

    +-------+-------+----------+------+
    | Part1 | Part2 | Plumbing | Base |
    +=======+=======+==========+======+
    |   d   | **f** |          |   ?  |
    +-------+-------+----------+------+
    | **f** |   d   |          |   ?  |
    +-------+-------+----------+------+

``finalize`` wins over any combination of ``default`` and ``extend``:

    +-------+-------+-------+----------+------+
    | Part1 | Part2 | Part3 | Plumbing | Base |
    +=======+=======+=======+==========+======+
    |   e   |   d   | **f** |          |   ?  |
    +-------+-------+-------+----------+------+
    |   d   |   e   | **f** |          |   ?  |
    +-------+-------+-------+----------+------+
    |   e   | **f** |   d   |          |   ?  |
    +-------+-------+-------+----------+------+
    |   d   | **f** |   e   |          |   ?  |
    +-------+-------+-------+----------+------+
    | **f** |   d   |   e   |          |   ?  |
    +-------+-------+-------+----------+------+
    | **f** |   e   |   e   |          |   ?  |
    +-------+-------+-------+----------+------+

Stage 2: Creation of Pipelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Declaration of a plumbing
^^^^^^^^^^^^^^^^^^^^^^^^^
A plumbing class inherits from base classes, declares the plumber as metaclass
and one or more Parts to be used by the plumber::

    >>> class Part2(Part):
    ...     pass

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2



A plumber in action
^^^^^^^^^^^^^^^^^^^


Instructions are processed in two stages: First



.. note:: Attributes


``plumber``
    Metaclass that creates a plumbing according to the instructions declared on
    plumbing parts. Instructions are given by decorators: ``default``,
    ``extend``, ``finalize``, ``plumb`` and ``plumbifexists``.

plumbing
    A plumber is called by a class that declares ``__metaclass__ = plumber``
    and a list of parts to be used for the plumbing ``__plumbing__ = Part1,
    Part2``. Apart from the parts, declarations on base classes and the class
    asking for the plumber are taken into account.  Once created a plumbing
    looks like any other class and can be subclassed as usual.

plumbing part
    A plumbing part provides attributes (functions, properties and plain values)
    along with instructions for how to use them. Instructions are given via
    decorators: ``default``, ``extend``, ``finalize``, ``plumb`` and
    ``plumbifexists``.

``default`` decorator
    Instruct the plumber to set a default value: first default wins, loses
    against base class declaration, ``extend`` and ``finalize``.

``extend`` decorator
    Instruct the plumber to set an attribute on the plumbing: first ``extend``
    wins, overrides ``default`` and base class, loses against ``finalize``.

``finalize`` decorator
    Instruct the plumber to definitely use an attribute value, overrides
``plumb`` decorator
    Instruct the plumber to make a function part of a plumbing chain and turns
    the function into a classmethod bound to the plumbing part declaring it
    with a signature of: ``def foo(_next, self, *args, **kw)``.
    ``prt`` is the part class declaring it, ``_next`` a wrapper for the next
    method in chain and ``self`` and instance of the plumbing
















Nomenclature
^^^^^^^^^^^^

raw plumbing class


``plumber``
    Metaclass that creates a plumbing according to the instructions declared on
    plumbing parts. Instructions are given by decorators: ``default``,
    ``extend``, ``finalize``, ``plumb`` and ``plumbifexists``.

plumbing
    A plumber is called by a class that declares ``__metaclass__ = plumber``
    and a list of parts to be used for the plumbing ``__plumbing__ = Part1,
    Part2``. Apart from the parts, declarations on base classes and the class
    asking for the plumber are taken into account.  Once created a plumbing
    looks like any other class and can be subclassed as usual.

plumbing part
    A plumbing part provides attributes (functions, properties and plain values)
    along with instructions for how to use them. Instructions are given via
    decorators: ``default``, ``extend``, ``finalize``, ``plumb`` and
    ``plumbifexists``.

``default`` decorator
    Instruct the plumber to set a default value: first default wins, loses
    against base class declaration, ``extend`` and ``finalize``.

``extend`` decorator
    Instruct the plumber to set an attribute on the plumbing: first ``extend``
    wins, overrides ``default`` and base class, loses against ``finalize``.

``finalize`` decorator
    Instruct the plumber to definitely use an attribute value, overrides
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

































.. contents::
    :backlinks: entry
    :depth: 2

Plumber
=======

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

The resolution of this funcionalities is done during a 2-phase parse of the
``__plumbing__`` chain.

1.) All ``default`` and ``extend`` are computed which define the ``endpoints``
of the plumbing.

2.) All ``pipelines`` are created. A single pipeline consists of a set of nested
closures which get called for defined endpoints.

2-Phase parse::

- iter[Part1, Part2, Part3] -> write endpoints
- iter[Part1, Part2, Part3] -> create pipelines


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

Resolution matrix for ``default``::

    +---------------+---------------------------------------+
    |               |  DEFAULT ENDPOINT RESOLUTION          |
    +---------------+---------+---------+---------+---------+
    | Endpoints     |  x(p)   |  y(b)   |  z(p1)  |  w(p2)  |
    +---------------+---------+---------+---------+---------+
    | Plumbing      |  x(p)   |         |         |         |
    +---------------+---------+---------+---------+---------+
    | Base          |  x(b)   |  y(b)   |         |         |
    +---------------+---------+---------+---------+---------+
    | Part1         |  x(p1)  |  y(p1)  |  z(p1)  |         |
    +---------------+---------+---------+---------+---------+
    | Part2         |  x(p2)  |  y(p2)  |  z(p2)  |  w(b2)  |
    +---------------+---------+---------+---------+---------+

Example::
    
    >>> from plumber import plumber
    >>> from plumber import Part
    >>> from plumber import default
    
    >>> class Part1(Part):
    ...     x = default('x(p1)')
    ...     y = default('y(p1)')
    ...     z = default('z(p1)')
    
    >>> class Part2(Part):
    ...     x = default('x(p2)')
    ...     y = default('y(p2)')
    ...     z = default('z(p2)')
    ...     w = default('w(p2)')
    
    >>> class Base(object):
    ...     x = 'x(b)'
    ...     y = 'y(b)'
    
    >>> class PlumbingClass(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...     x = 'x(p)'
    
Console::

    >>> plumbing = PlumbingClass()
    >>> plumbing.x
    'x(p)'
    >>> plumbing.y
    'y(b)'
    >>> plumbing.z
    'z(p1)'
    >>> plumbing.w
    'w(p2)'


Defining extensions
-------------------

The ``extend`` decorator is used to explicitly define functions, properties and
attribues as endpoints for a plumbing which are immutable.

They overwrite existing functions, properties and attribues defined by
``default`` decorator.

They must not be overwritten by another part, this raises an error.

Use ``extend`` decorator if you know that a function must not be overwritten
by anything else, like storage related stuff, et cetera.

Resolution matrix for ``extend``::
    
    +---------------+-------------------------------------------------+
    |               |  EXTEND ENDPOINT RESOLUTION                     |
    +---------------+---------+---------+---------+---------+---------+
    | Endpoints     |  x(p)   |  y(p1)  |  z(p2)  |  w(p3)  |  v(p4)  |
    +---------------+---------+---------+---------+---------+---------+
    | Plumbing      |  x(p)   |         |         |         |         |
    +---------------+---------+---------+---------+---------+---------+
    | Part1         |         |  y(p1)  |         |         |         |
    +---------------+---------+---------+---------+---------+---------+
    | Part2         |         |         |  z(p2)  |         |         |
    +---------------+---------+---------+---------+---------+---------+
    | Part3         |         |         |         |  w(p3)  |         |
    +---------------+---------+---------+---------+---------+---------+
    | Base          |  x(b)   |  y(b)   |  z(b)   |  w(b)   |  v(b)   |
    +---------------+---------+---------+---------+---------+---------+

Example::

    >>> from plumber import plumber
    >>> from plumber import Part
    >>> from plumber import extend
    
    >>> class Part1(Part):
    ...     y = extend('y(p1)')
    
    >>> class Part2(Part):
    ...     z = extend('z(p2)')
    
    >>> class Part3(Part):
    ...     w = extend('w(p3)')
    
    >>> class Base(object):
    ...     x = 'x(b)'
    ...     y = 'y(b)'
    ...     z = 'z(b)'
    ...     w = 'w(b)'
    ...     v = 'v(b)' 
    
    >>> class PlumbingClass(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2, Part3
    ...     x = 'x(p)'

Console::
    
    >>> plumbing = PlumbingClass()
    >>> plumbing.x
    'x(p)'
    >>> plumbing.y
    'y(p1)'
    >>> plumbing.z
    'z(p2)'
    >>> plumbing.w
    'w(p3)'
    >>> plumbing.v
    'v(b)'


Defining pipelines
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

Console::

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
-------------------------------------

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


Subclass gets its own stacks
----------------------------

::
    >>> class Part1(Part):
    ...     a = extend(1)

    >>> class Base(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1

    >>> class Sub(Base):
    ...     __plumbing__ = Part1


Passing parameters to methods in a plumbing chain
-------------------------------------------------

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
------------------------------

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


Plumbing for property getter, setter and deleter
------------------------------------------------

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
A base class with a full property::

    >>> def set_a(self, val):
    ...     self._a = val

    >>> def del_a(self):
    ...     del self._a

    >>> class Base(object):
    ...     a = property(
    ...          lambda self: self._a,
    ...          set_a,
    ...          del_a,
    ...          "doc_a",
    ...          )

A part that plumbs into all aspects of the property (getter, setter, deleter,
doc)::

    >>> class Notify(Part):
    ...     def get_a(_next, self):
    ...         print "Getting a"
    ...         return _next(self)
    ...     def set_a(_next, self, val):
    ...         print "Setting a"
    ...         _next(self, val)
    ...     def del_a(_next, self):
    ...         print "Deleting a"
    ...         _next(self)
    ...     a = plumb(property(
    ...         get_a,
    ...         set_a,
    ...         del_a,
    ...         "notify",
    ...         ))

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Notify

The docstring is plumbed::

    >>> print Plumbing.a.__doc__
    notify
    doc_a

    >>> plumbing = Plumbing()

So are getter, setter and deleter::

    >>> hasattr(plumbing, '_a')
    False
    >>> plumbing.a = 8
    Setting a
    >>> plumbing.a
    Getting a
    8
    >>> hasattr(plumbing, '_a')
    True
    >>> del plumbing.a
    Deleting a
    >>> hasattr(plumbing, '_a')
    False




A base class has a readonly property, a plumbing property plumbs in::

    >>> class Base(object):
    ...     _foo = 5
    ...     @property
    ...     def foo(self):
    ...         return self._foo

    >>> class Part1(Part):
    ...     @plumb
    ...     @property
    ...     def foo(_next, self):
    ...         return 3 * _next(self)

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1

    >>> plumbing = Plumbing()
    >>> plumbing.foo
    15
    >>> plumbing.foo = 10
    Traceback (most recent call last):
     ...
    AttributeError: can't set attribute


Extending a class
-----------------
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

#XXX#     >>> class PlumbingClass(object):
#XXX#     ...     __metaclass__ = plumber
#XXX#     ...     __plumbing__ = Part1
#XXX#     ...     foo = False
#XXX#     Traceback (most recent call last):
#XXX#       ...
#XXX#     PlumbingCollision:
#XXX#         Plumbing class
#XXX#       with:
#XXX#         <extend 'foo' of <class 'Part1'> payload=False>

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

#XXX#     >>> class Part1(Part):
#XXX#     ...     foo = extend(False)
#XXX# 
#XXX#     >>> class Part2(Part):
#XXX#     ...     foo = extend(True)
#XXX# 
#XXX#     >>> class PlumbingClass(object):
#XXX#     ...     __metaclass__ = plumber
#XXX#     ...     __plumbing__ = Part1, Part2
#XXX#     Traceback (most recent call last):
#XXX#       ...
#XXX#     PlumbingCollision:
#XXX#         <extend 'foo' of <class 'Part1'> payload=False>
#XXX#       with:
#XXX#         <extend 'foo' of <class 'Part2'> payload=True>

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

#XXX#     >>> class PlumbingClass(object):
#XXX#     ...     __metaclass__ = plumber
#XXX#     ...     __plumbing__ = Part1, Part2, Part3
#XXX#     Traceback (most recent call last):
#XXX#       ...
#XXX#     PlumbingCollision:
#XXX#         <extend 'foo' of <class 'Part1'> payload=<function foo at 0x...>>
#XXX#       with:
#XXX#         <extend 'foo' of <class 'Part3'> payload=<function foo at 0x...>>

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
------------------

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
-------------------------

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


Contributors
------------

- Florian Friesdorf <flo@chaoflow.net>
- Robert Niederreiter <rnix@squarewave.at>
- Jens W. Klein <jens@bluedynamics.com>
- Attila Oláh
- thanks to WSGI for the concept
- thanks to #python (for trying) to block stupid ideas


Changes
-------

- ``.. plbnext::`` instead of ``.. plb_next::``
  [chaoflow 2011-02-02]

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
----

- traceback should show in which plumbing class we are, not something inside
  the plumber. yafowil is doing it. jensens: would you be so kind.
- verify behaviour with pickling
- verify behaviour with ZODB persistence
- subclassing for plumbing parts
- plumbing of property getter, setter and deleter for non-lambda properties


Disclaimer
----------

TODO
