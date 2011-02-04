Plumber
=======

Plumbing is an alternative to mixin-based extension of classes.  In motivation
an incomplete list of limitations and/or design choices of python's subclassing
are given along with plumber's solutions for them. The plumbing system is
described in detail with code examples. Some design choices and ongoing
discussions are explained. Finally, in miscellanea you find nomenclature,
coverage report, list of contributors, changes and some todos.  All
non-experimental features are fully test covered.

.. contents::
    :depth: 2

Motivation: limitations of subclassing
--------------------------------------

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


The plumbing system
-------------------

The ``plumber`` metaclass creates plumbing classes according to instructions
found on plumbing parts. First, all instructions are gathered, then they are
applied in two stages: stage1: extension and stage2: pipelines, docstrings and
optional ``zope.interfaces``.

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

    >>> Base = dict
    >>> class Plumbing(Base):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...
    ...     def foobar(self):
    ...         return 5

The result is a plumbing class created according to the plumbing declaration::

    >>> plb = Plumbing()
    >>> plb.a
    True
    >>> plb.foo()
    42
    >>> plb.bar
    17
    >>> plb.foobar()
    5
    >>> plb['a'] = 1
    >>> plb['a']
    1

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

Before putting a new instruction onto a stack, it is compared with the latest
instruction on the stack. It is either taken as is, discarded, merged or a
``PlumbingCollision`` is raised. This is detailed in the following sections.

After all instructions are gathered onto the stacks, they are applied in two
stages taking declarations on the plumbing class and base classes into account.

The result of the first stage is the base for the application of the second
stage.

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

Stage 1: Extension
^^^^^^^^^^^^^^^^^^
The extension stage creates endpoints for the pipelines created in stage 2. If
no pipeline uses the endpoint, it will just live on as a normal attribute in
the plumbing class' dictionary.

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
``super``-chains. Docstrings of parts, methods in a pipeline and properties in
a pipeline are accumulated. Plumber is ``zope.interface`` aware and takes
implemeneted interfaces from parts, if it can be imported.

.. contents::
    :local:

Plumbing Pipelines in general
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Elements for plumbing pipelines are declared with the ``plumb`` and
``plumbifexists`` decorators:

``plumb``
    Marks a method to be used as part of a plumbing pipeline.  The signature of
    such a plumbing method is ``def foo(_next, self, *args, **kw)``.  Via
    ``_next`` it is passed the next plumbing method to be called. ``self`` is
    an instance of the plumbing class, not the part.

``plumbifexists``
    Like ``plumb``, but only used if an endpoint exists.

The user of a plumbing class does not know which ``_next`` to pass. Therefore,
after the pipelines are built, an entrance method is generated for each pipe,
that wraps the first plumbing method passing it the correct ``_next``. Each
``_next`` method is an entrance to the rest of the pipeline.




The pipelines are build in part order, skipping parts that do not define a
pipeline element with the same attribute name::

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
    | S |       |       |   z   |    z     |
    |   |       |       |    <-------      |
    +---+-------+-------+-------+----------+

Method pipelines
~~~~~~~~~~~~~~~~
Two plumbing parts and a ``dict`` as base class. ``Part1`` lowercases keys
before passing them on, ``Part2`` multiplies results before returning them::

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
    >>> plb['AbC']
    Part1 start
    Part2 start
    Part2 stop
    Part1 stop
    12

Plumbing pipelines need endpoints. If no endpoint is available an
``AttributeError`` is raised::

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

If no endpoint is available and a part does not care about that,
``plumbifexists`` can be used to only plumb if an endpoint is available::

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

This enables one implementation of a certain behaviour, e.g. sending events for
dictionaries, to be used for readwrite dictionaries that implement
``__getitem__`` and ``__setitem__`` and readonly dictionaries, that only
implement ``__getitem__`` but no ``__setitem__``.

Property pipelines
~~~~~~~~~~~~~~~~~~
Plumbing of properties is experimental and might or might not do what you
expect::

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

    >>> plb = Plumbing()
    >>> plb.foo
    6

It is possible to extend a property with so far unset getter/setter/deleter.
The feature is experimental, might not fit the expected behavior and probably
about to change::

    >>> class Part1(Part):
    ...     @plumb
    ...     @property
    ...     def foo(_next, self):
    ...         return 2 * _next(self)

    >>> class Part2(Part):
    ...     def set_foo(self, value):
    ...         self._foo = value
    ...     foo = plumb(property(
    ...         None,
    ...         extend(set_foo),
    ...         ))

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Part1, Part2
    ...
    ...     @property
    ...     def foo(self):
    ...         return self._foo

    >>> plb = Plumbing()
    >>> plb.foo = 4
    >>> plb.foo
    8

Mixing methods and properties within the same pipeline is not possible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

docstrings of classes, methods and properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Normal docstrings of the plumbing declaration and the part classes, plumbed
methods and plumbed properties are joined by newlines starting with the
plumbing declaration and followed by the parts in reverse order::

    >>> class P1(Part):
    ...     """P1
    ...     """
    ...     @plumb
    ...     def foo(self):
    ...         """P1.foo
    ...         """
    ...     bar = plumb(property(None, None, None, "P1.bar"))

    >>> class P2(Part):
    ...     @extend
    ...     def foo(self):
    ...         """P2.foo
    ...         """
    ...     bar = plumb(property(None, None, None, "P2.bar"))

    >>> class Plumbing(object):
    ...     """Plumbing
    ...     """
    ...     __metaclass__ = plumber
    ...     __plumbing__ = P1, P2
    ...     bar = property(None, None, None, "Plumbing.bar")

    >>> print Plumbing.__doc__
    Plumbing
    <BLANKLINE>
    P1
    <BLANKLINE>

    >>> print Plumbing.foo.__doc__
    P2.foo
    <BLANKLINE>
    P1.foo
    <BLANKLINE>

    >>> print Plumbing.bar.__doc__
    Plumbing.bar
    <BLANKLINE>
    P2.bar
    <BLANKLINE>
    P1.bar

The accumulation of docstrings is an experimental feature and will probably
change.


``zope.interface`` (if available)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The plumber does not depend on ``zope.interface`` but is aware of it. That
means it will try to import it and if available will check plumbing parts for
implemented interfaces and will make the plumbing implement them, too::

    >>> from zope.interface import Interface
    >>> from zope.interface import implements

A class with an interface that will serve as base class of a plumbing::

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

Design choices and ongoing discussions
--------------------------------------

Stage1 left of stage2
^^^^^^^^^^^^^^^^^^^^^
Currently instructions of stage1 may be left of stage2 instructions. We
consider to forbid this::

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

Instance based plumbing system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
At various points it felt tempting to be able to instantiate plumbing elements
to configure them. For that we need ``__init__``, which woul mean that plumbing
``__init__`` would need a different name, eg. ``prt_``-prefix. Consequently
this would then be done for all plumbing methods.

Reasoning why currently the methods are not prefixed:
Plumbing elements are simply not meant to be normal classes. Their methods have
the single purpose to be called as part of some other class' method calls,
never directly. Configuration of plumbing elements can either be achieved by
subclassing them or by putting the configuration on the objects/class they are
used for.

An instance based plumbing system would be far more complex. It could be
implemented to exist alongside the current system. But it won't be implemented
by us, without seeing a real use case first.

Different zope.interface.Interfaces for plumbing and created class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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

Dynamic Plumbing
^^^^^^^^^^^^^^^^
The plumber could replace the ``__plumbing__`` attribute with a property of the
same name. Changing the attribute during runtime would result in a plumbing
specific to the object. A plumbing cache could further be used to reduce the
number of plumbing chains in case of many dynamic plumbings. Realised eg by a
descriptor.

During discussion on the artssprint we agreed on not changing a plumbing class
pipelines during runtime, but instead enable plumbing further parts during
runtime per instance in front of the class' pipeline.

Miscellanea
-----------

Nomenclature
^^^^^^^^^^^^
``plumber``
    Metaclass that creates a plumbing according to the instructions declared on
    plumbing parts. Instructions are given by decorators: ``default``,
    ``extend``, ``finalize``, ``plumb`` and ``plumbifexists``.

plumbing
    A plumber is called by a class that declares ``__metaclass__ = plumber``
    and a list of parts to be used for the plumbing ``__plumbing__ = Part1,
    Part2``. Apart from the parts, declarations on base classes and the class
    asking for the plumber are taken into account.  Once created, a plumbing
    looks like any other class and can be subclassed as usual.

plumbing part
    A plumbing part provides attributes (functions, properties and plain values)
    along with instructions for how to use them. Instructions are given via
    decorators: ``default``, ``extend``, ``finalize``, ``plumb`` and
    ``plumbifexists`` (see Stage 1:... and Stage 2:...).

plumbing pipeline
    Plumbing methods/properties with the same name form a pipeline. The
    entrance and end-point have the signature of normal methods: ``def
    foo(self, *args, **kw)``. The plumbing pipelines is a series of nested
    closures (see ``_next``).

entrance (method)
    A method with a normal signature. i.e. expecting ``self`` as first
    argument, that is used to enter a pipeline. It is a ``_next`` function. A
    method declared on the class with the same name, will be overwritten, but
    referenced in the pipelines as the innermost method, the endpoint.

``_next`` function
    The ``_next`` function is used to call the next method in a pipelines: in
    case of a plumbing method, it is a wrapper of it that passes the correct
    next ``_next`` as first argument and in case of an end-point, just the
    end-point method itself.

end-point (method)
    Method retrieved from the plumbing class with ``getattr()``, before setting
    the entrance method on the class.

If you feel something is missing, please let us now or write a short
corresponding text.

Test Coverage
^^^^^^^^^^^^^
Summary of the test coverage report::

    lines   cov%   module   (path)
        7   100%   plumber.__init__
      187   100%   plumber._instructions
       49    91%   plumber._part
       58   100%   plumber._plumber
        9   100%   plumber.exceptions
       18   100%   plumber.tests._globalmetaclasstest
       18   100%   plumber.tests.test_


Contributors
^^^^^^^^^^^^
- Florian Friesdorf <flo@chaoflow.net>
- Robert Niederreiter <rnix@squarewave.at>
- Jens W. Klein <jens@bluedynamics.com>
- Marco Lempen
- Attila Oláh
- thanks to WSGI for the initial concept
- thanks to #python (for trying) to block stupid ideas, if there are any left,
  please let us know


Changes
^^^^^^^
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
^^^^
- traceback should show in which plumbing class we are, not something inside
  the plumber. yafowil is doing it. jensens: would you be so kind.
- verify behaviour with pickling in tests within plumber
- verify behaviour with ZODB persistence in tests within plumber
- subclassing for plumbing parts
- mature plumbing of properties
- py26 @foo.setter support in all decorators


License / Disclaimer
^^^^^^^^^^^^^^^^^^^^
Copyright (c) 2011, BlueDynamics Alliance, Austria, Germany, Switzerland
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation and/or
  other materials provided with the distribution.
* Neither the name of the BlueDynamics Alliance nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY BlueDynamics Alliance ``AS IS`` AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL BlueDynamics Alliance BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
