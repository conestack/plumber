Plumber
=======

XXX: Intro

XXX: Missing for release?

- C3 resolution for instructions from plumbing part bases
- docstring behaviour
- adding a so far unset property function (extend?)

.. contents::
    :depth: 3

Motivation
----------

Plumbing is an alternative to mixin-based extension of classes, motivated by
limitations and/or design choice of python's subclassing:

.. contents::
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

``super``-chains are not verified during class creation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
is no endpoint an ``AttributeError`` is raised during runtime, not during class
creation::

    >>> class Mixin1(object):
    ...     def foo(self):
    ...         super(Mixin1, self).foo()

    >>> class MixedClass(Mixin1, Base):
    ...     pass

    >>> mc = MixedClass()
    >>> mc.foo()
    Traceback (most recent call last):
      ...
    AttributeError: 'super' object has no attribute 'foo'

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
``__plbnext__``, which is replaced with the docstring of the next "mixin"
Without the marker, docstrings are concatenated.

.. warning:: The ``__plbnext__`` feature is experimental and might change


The plumbing system
-------------------

The ``plumber`` metaclass creates plumbing classes according to instructions
found on plumbing parts.

XXX:

.. contents::
    :local:

Plumbing parts provide instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Plumbing parts correspond to mixins, but are more powerful and flexible. A
plumbing part needs to inherit from ``plumber.Part`` and declares attributes
with instructions on how to use them, here by example of the ``default``
instruction (more later)::

    >>> from plumber import Part
    >>> from plumber import default

    >>> class Part1(Part):
    ...     a = default(True)
    ...
    ...     @default
    ...     def foo(self):
    ...         return 42

    >>> class Part2(Part):
    ...     @default
    ...     @property
    ...     def bar(self):
    ...         return 17

The instructions are given as part of assignments (``a = default(None)``) or as
decorators (``@default``).

A plumbing declaration defines the ``plumber`` as metaclass and one or more
plumbing parts to be processed from left to right. Further it may declare
attributes like every normal class, they will be treated as implicit
``finalize`` instructions (see Stage 1: Extension)::

    >>> from plumber import plumber

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...
    ...     def foobar(self):
    ...         return 5

The result is a plumbing class created according to the plumbing declaration::

    >>> Plumbing.a
    True
    >>> Plumbing().foo()
    42
    >>> Plumbing().bar
    17
    >>> Plumbing().foobar()
    5

A plumbing class can be subclassed like normal classes::

    >>> class Sub(Plumbing):
    ...     a = 'Sub'

    >>> Sub.a
    'Sub'
    >>> Sub().foo()
    42
    >>> Sub().bar
    17
    >>> Sub().foobar()
    5

The plumber gathers instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A plumbing declaration provides a list of parts via the ``__plumbing__``
attribute. Parts provide instructions to be applied in two stages:

stage1
  - extension via ``default``, ``extend`` and ``finalize``, the result of this
    stage is the base for stage2.

stage2
  - creation of pipelines via ``plumb`` and ``plumbifexists``
  - plumbing of docstrings
  - implemented interfaces from ``zope.interface``, iff available

The plumber walks the part list from left to right (part order). On its way it
gathers instructions onto stacks, sorted by stage and attribute name. A history
of all instructions is kept::

    >>> pprint(Plumbing.__plumbing_stacks__)
    {'history':
      [<_implements '__interfaces__' of None payload=()>,
       <default 'a' of <class 'Part1'> payload=True>,
       <default 'foo' of <class 'Part1'> payload=<function foo at 0x...>>,
       <_implements '__interfaces__' of None payload=()>,
       <default 'bar' of <class 'Part2'> payload=<property object at 0x...>>],
     'stages':
       {'stage1':
         {'a': [<default 'a' of <class 'Part1'> payload=True>],
          'bar': [<default 'bar' of <class 'Part2'> payload=<property ...
          'foo': [<default 'foo' of <class 'Part1'> payload=<function foo ...
        'stage2':
         {'__interfaces__': [<_implements '__interfaces__' of None payload=()...

.. note:: The payload of an instruction is the attribute value passed to the
  instruction via function call or decoration. An instruction knows the part it
  is declared on.

.. note:: Parts are created by ``partmetaclass``. If ``zope.interface`` is
  available, it will generate ``_implements`` instructions for each part.
  During part creation the interfaces are not yet implemented, they are checked
  at a later stage. Therefore the ``_implements`` instructions are generated
  even if the parts do not implement interfaces, which results in the empty
  tuple as payload (see also ``zope.interface support``.

.. warning:: Do not rely on this structure within your programs it might change
  at any time. If you need information from the ``__plumbing_stacks__`` or lack
  information in there, e.g. to create a plumbing inspector and earn yourself
  a box of your favorite beverage, please let us know.

Before putting a new instruction onto a stack, it is compared with the latest
instruction on the stack. It is either taken as is, discarded, merged or a
``PlumbingCollision`` is raised. This is detailed in the following sections.

After all instructions are gathered onto the stacks, they are applied in two
stages taking declarations on the plumbing class and base classes into account.

The result of the first stage is the base for the application of the second
stage.

Stage 1: Extension
^^^^^^^^^^^^^^^^^^
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

``extend``
    ``extend`` is weaker than ``finalize`` and overrides declarations on base
    classes and ``default`` declarations. Two ``extend`` instructions for the
    same attribute name do not collide, instead the first one will be used.

``default``
    ``default`` is the weakest extension instruction. It will not even override
    declarations of base classes. The first default takes precendence over
    later defaults.

.. contents::
    :local:

Interaction: ``finalize``, plumbing declaration and base classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In code::

    >>> from plumber import finalize

    >>> class Part1(Part):
    ...     N = finalize('Part1')
    ...

    >>> class Part2(Part):
    ...     M = finalize('Part2')

    >>> class Base(object):
    ...     K = 'Base'

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...     L = 'Plumbing'

    >>> for x in ['K', 'L', 'M', 'N']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Base
    L from Plumbing
    M from Part2
    N from Part1

summary:

- K-Q: attributes defined by parts, plumbing class and base classes
- f: ``finalize`` declaration
- x: declaration on plumbing class or base class
- ?: base class declaration is irrelevant
- **Y**: chosen end point
- collision: indicates an invalid combination, that raises a ``PlumbingCollision``

+-------+-------+-------+----------+-------+-----------+
| Attr  | Part1 | Part2 | Plumbing | Base  |    ok?    |
+=======+=======+=======+==========+=======+===========+
|   K   |       |       |          | **x** |           |
+-------+-------+-------+----------+-------+-----------+
|   L   |       |       |  **x**   |   ?   |           |
+-------+-------+-------+----------+-------+-----------+
|   M   |       | **f** |          |   ?   |           |
+-------+-------+-------+----------+-------+-----------+
|   N   | **f** |       |          |   ?   |           |
+-------+-------+-------+----------+-------+-----------+
|   O   |   f   |       |    x     |   ?   | collision |
+-------+-------+-------+----------+-------+-----------+
|   P   |       |   f   |    x     |   ?   | collision |
+-------+-------+-------+----------+-------+-----------+
|   Q   |   f   |   f   |          |   ?   | collision |
+-------+-------+-------+----------+-------+-----------+

collisions::

    >>> class Part1(Part):
    ...     O = finalize(False)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    ...     O = True
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        Plumbing class
      with:
        <finalize 'O' of <class 'Part1'> payload=False>

    >>> class Part2(Part):
    ...     P = finalize(False)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part2
    ...     P = True
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        Plumbing class
      with:
        <finalize 'P' of <class 'Part2'> payload=False>

    >>> class Part1(Part):
    ...     Q = finalize(False)

    >>> class Part2(Part):
    ...     Q = finalize(True)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        <finalize 'Q' of <class 'Part1'> payload=False>
      with:
        <finalize 'Q' of <class 'Part2'> payload=True>

Interaction: ``extend``, plumbing declaration and base classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
in code::

    >>> from plumber import extend

    >>> class Part1(Part):
    ...     K = extend('Part1')
    ...     M = extend('Part1')

    >>> class Part2(Part):
    ...     K = extend('Part2')
    ...     L = extend('Part2')
    ...     M = extend('Part2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'
    ...     M = 'Base'

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...     K = 'Plumbing'

    >>> for x in ['K', 'L', 'M']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Plumbing
    L from Part2
    M from Part1

summary:

- K-M: attributes defined by parts, plumbing class and base classes
- e: ``extend`` declaration
- x: declaration on plumbing class or base class
- ?: base class declaration is irrelevant
- **Y**: chosen end point

+-------+-------+-------+----------+-------+
| Attr  | Part1 | Part2 | Plumbing | Base  |
+=======+=======+=======+==========+=======+
|   K   |   e   |   e   |  **x**   |   ?   |
+-------+-------+-------+----------+-------+
|   L   |       | **e** |          |   ?   |
+-------+-------+-------+----------+-------+
|   M   | **e** |   e   |          |   ?   |
+-------+-------+-------+----------+-------+

Interaction: ``default``, plumbing declaration and base class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
in code::

    >>> class Part1(Part):
    ...     N = default('Part1')

    >>> class Part2(Part):
    ...     K = default('Part2')
    ...     L = default('Part2')
    ...     M = default('Part2')
    ...     N = default('Part2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...     L = 'Plumbing'

    >>> for x in ['K', 'L', 'M', 'N']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Base
    L from Plumbing
    M from Part2
    N from Part1

summary:

- K-N: attributes defined by parts, plumbing class and base classes
- d = ``default`` declaration
- x = declaration on plumbing class or base class
- ? = base class declaration is irrelevant
- **Y** = chosen end point

+-------+-------+-------+----------+-------+
| Attr  | Part1 | Part2 | Plumbing | Base  |
+=======+=======+=======+==========+=======+
|   K   |       |   d   |          | **x** |
+-------+-------+-------+----------+-------+
|   L   |       |   d   |  **x**   |   ?   |
+-------+-------+-------+----------+-------+
|   M   |       | **d** |          |       |
+-------+-------+-------+----------+-------+
|   N   | **d** |   d   |          |       |
+-------+-------+-------+----------+-------+


Interaction: ``finalize`` wins over ``extend``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
in code::

    >>> class Part1(Part):
    ...     K = extend('Part1')
    ...     L = finalize('Part1')

    >>> class Part2(Part):
    ...     K = finalize('Part2')
    ...     L = extend('Part2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2

    >>> for x in ['K', 'L']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Part2
    L from Part1

summary:

- K-L: attributes defined by parts, plumbing class and base classes
- e = ``extend`` declaration
- f = ``finalize`` declaration
- ? = base class declaration is irrelevant
- **Y** = chosen end point

+-------+-------+-------+----------+------+
| Attr  | Part1 | Part2 | Plumbing | Base |
+=======+=======+=======+==========+======+
|   K   |   e   | **f** |          |   ?  |
+-------+-------+-------+----------+------+
|   L   | **f** |   e   |          |   ?  |
+-------+-------+-------+----------+------+

Interaction: ``finalize`` wins over ``default``:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
in code::

    >>> class Part1(Part):
    ...     K = default('Part1')
    ...     L = finalize('Part1')

    >>> class Part2(Part):
    ...     K = finalize('Part2')
    ...     L = default('Part2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2

    >>> for x in ['K', 'L']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Part2
    L from Part1

summary:

- K-L: attributes defined by parts, plumbing class and base classes
- d = ``default`` declaration
- f = ``finalize`` declaration
- ? = base class declaration is irrelevant
- **Y** = chosen end point

+-------+-------+-------+----------+------+
| Attr  | Part1 | Part2 | Plumbing | Base |
+=======+=======+=======+==========+======+
|   K   |   d   | **f** |          |   ?  |
+-------+-------+-------+----------+------+
|   L   | **f** |   d   |          |   ?  |
+-------+-------+-------+----------+------+

Interaction: ``extend`` wins over ``default``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
in code::

    >>> class Part1(Part):
    ...     K = default('Part1')
    ...     L = extend('Part1')

    >>> class Part2(Part):
    ...     K = extend('Part2')
    ...     L = default('Part2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'

    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2

    >>> for x in ['K', 'L']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Part2
    L from Part1

summary:

- K-L: attributes defined by parts, plumbing class and base classes
- d = ``default`` declaration
- e = ``extend`` declaration
- ? = base class declaration is irrelevant
- **Y** = chosen end point

+-------+-------+-------+----------+------+
| Attr  | Part1 | Part2 | Plumbing | Base |
+=======+=======+=======+==========+======+
|   K   |   d   | **e** |          |   ?  |
+-------+-------+-------+----------+------+
|   L   | **e** |   d   |          |   ?  |
+-------+-------+-------+----------+------+

Stage 2: Pipeline, docstring and ``zope.interface`` instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In stage1 plumbing class attributes were set, which can serve as endpoints for
plumbing pipelines that are build in stage2. Plumbing pipelines correspond to
``super``-chains. Elements for plumbing pipelines are declared with the
``plumb`` and ``plumbifexists`` decorators.

``plumb``
    Marks a method to be used as part of a plumbing pipeline. The signature of
    such a plumbing method is ``def foo(_next, self, *args, **kw)``. Via
    ``_next`` it is passed the next plumbing method to be called.

``plumbifexists``
    Like ``plumb``, but only used if an endpoint exists.

XXX: explain entrance

XXX

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

.. contents::
    :local:

Method pipelines
~~~~~~~~~~~~~~~~
    >>> from plumber import plumb

    >>> class Part1(Part):
    ...     @plumb
    ...     def __getitem__(_next, self, key):
    ...         print "Part1 start"
    ...         key = key.lower()
    ...         ret = _next(self, key)
    ...         print "Part1 stop"
    ...         return ret

    >>> class Part2(Part):
    ...     @plumb
    ...     def __getitem__(_next, self, key):
    ...         print "Part2 start"
    ...         ret = 2 * _next(self, key)
    ...         print "Part2 stop"
    ...         return ret

    >>> Base = dict
    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2

    >>> plb = Plumbing()
    >>> plb['abc'] = 6
    >>> plb['ABC']
    Part1 start
    Part2 start
    Part2 stop
    Part1 stop
    12

Plumbing pipelines need endpoints. If no endpoint is available an
``AttributeError`` is raised.

    >>> class Part1(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         pass

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    Traceback (most recent call last):
      ...     
    AttributeError: type object 'Plumbing' has no attribute 'foo'

``plumbifexists``

    >>> from plumber import plumbifexists

    >>> class Part1(Part):
    ...     @plumbifexists
    ...     def foo(_next, self):
    ...         pass
    ...
    ...     @plumbifexists
    ...     def bar(_next, self):
    ...         return 2 * _next(self)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    ...
    ...     def bar(self):
    ...         return 6

    >>> hasattr(Plumbing, 'foo')
    False
    >>> Plumbing().bar()
    12
    
Property pipelines
~~~~~~~~~~~~~~~~~~
    >>> class Part1(Part):
    ...     @plumb
    ...     @property
    ...     def foo(_next, self):
    ...         return 2 * _next(self)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    ...
    ...     @property
    ...     def foo(self):
    ...         return 3

    >>> Plumbing().foo
    6



    #    >>> class Part1(Part):
    #    ...     @plumb
    #    ...     @property
    #    ...     def foo(_next, self):
    #    ...         return 2 * _next(self)
    #
    #    >>> class Part2(Part):
    #    ...     def set_foo(self, value):
    #    ...         self._foo = value
    #    ...     foo = plumb(property(
    #    ...         None,
    #    ...         extend(set_foo),
    #    ...         ))
    #
    #    >>> class Plumbing(object):
    #    ...     __metaclass__ = plumber
    #    ...     __plumbing__ = Part1, Part2
    #    ...
    #    ...     @property
    #    ...     def foo(self):
    #    ...         return self._foo
    #
    #    >>> Plumbing().foo = 4
    #    >>> Plumbing().foo

Methods and properties within the same pipeline are invalid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Within a pipeline all elements need to be of the same type, it is not possible
to mix properties with methods::

    >>> from plumber import plumb

    >>> class Part1(Part):
    ...     @plumb
    ...     def foo(_next, self):
    ...         return _next(self)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1
    ...
    ...     @property
    ...     def foo(self):
    ...         return 5
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        <plumb 'foo' of <class 'Part1'> payload=<function foo at 0x...>>
      with:
        <class 'Plumbing'>

docstrings
~~~~~~~~~~

Experimental feature, intentionally undocumented.


``zope.interface``
~~~~~~~~~~~~~~~~~~

The plumber does not depend on ``zope.interface`` but is aware of it. That
means it will try to import it and if available will check plumbing parts for
implemented interfaces and will make the plumbing class implement them, too::

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

A plumbing based on ``Base`` using ``Part1`` and ``Part2`` and implementing
``IPlumbingClass``::

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
possible to base classes of our class, but without using subclassing. For an
additional maybe future approach see Discussion.

XXX





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

Design choices
--------------

Currently instructions of stage1 may be left of stage2 instructions. We
consider to forbid this. For now a warning is raised if you do it::

    #    >>> class Part1(Part):
    #    ...     @extend
    #    ...     def foo(self):
    #    ...         return 5
    #
    #    >>> class Part2(Part):
    #    ...     @plumb
    #    ...     def foo(_next, self):
    #    ...         return 2 * _next(self)
    #
    #    >>> class Plumbing(object):
    #    ...     __metaclass__ = plumber
    #    ...     __plumbing__ = Part1, Part2
    #
    #    >>> Plumbing().foo()
    #    BANG

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
- Marco Lempen
- Attila Oláh
- thanks to WSGI for the initial concept
- thanks to #python (for trying) to block stupid ideas, if there are any left,
  please let us know


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
