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
following mixins and the base class being extended.

.. code-block:: pycon

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
precedence (``default``, ``override``, ``finalize``).


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
before returning it and both are chatty about start/stop.

.. code-block:: pycon

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
creation.

.. code-block:: pycon

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
found on plumbing behaviors. First, all instructions are gathered, then they are
applied in two stages: stage1: extension and stage2: pipelines, docstrings and
optional ``zope.interfaces``. There exists a class decorator ``plumbing`` which
should be used in favor of setting metaclass directly as of plumber 1.3.

.. contents::
    :local:


Plumbing behaviors provide instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Plumbing behaviors correspond to mixins, but are more powerful and flexible. A
plumbing behavior needs to inherit from ``plumber.Behavior`` and declares 
attributes with instructions on how to use them, here by example of the 
``default`` instruction (more later).

.. code-block:: pycon

    >>> from plumber import Behavior
    >>> from plumber import default

    >>> class Behavior1(Behavior):
    ...     a = default(True)
    ...
    ...     @default
    ...     def foo(self):
    ...         return 42

    >>> class Behavior2(Behavior):
    ...     @default
    ...     @property
    ...     def bar(self):
    ...         return 17

The instructions are given as behavior of assignments (``a = default(None)``) 
or as decorators (``@default``).

A plumbing declaration defines the ``plumber`` as metaclass and one or more
plumbing behaviors to be processed from left to right. Further it may declare
attributes like every normal class, they will be treated as implicit
``finalize`` instructions (see Stage 1: Extension).

.. code-block:: pycon

    >>> from plumber import plumbing

    >>> Base = dict

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(Base):
    ...
    ...     def foobar(self):
    ...         return 5

The result is a plumbing class created according to the plumbing declaration.

.. code-block:: pycon

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

A plumbing class can be subclassed like normal classes.

.. code-block:: pycon

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

A plumbing declaration provides a list of behaviors via the ``plumbing``
decorator. Behaviors provide instructions to be applied in two stages:

stage1
  - extension via ``default``, ``override`` and ``finalize``, the result of this
    stage is the base for stage2.

stage2
  - creation of pipelines via ``plumb`` and ``plumbifexists``
  - plumbing of docstrings
  - implemented interfaces from ``zope.interface``, iff available

The plumber walks the Behavior list from left to right (behavior order). On its
way it gathers instructions onto stacks, sorted by stage and attribute name. A 
history of all instructions is kept.

.. code-block:: pycon

    >>> pprint(Plumbing.__plumbing_stacks__)
    {'history':
      [<_implements '__interfaces__' of None payload=()>,
       <default 'a' of <class 'Behavior1'> payload=True>,
       <default 'foo' of <class 'Behavior1'> payload=<function foo at 0x...>>,
       <_implements '__interfaces__' of None payload=()>,
       <default 'bar' of <class 'Behavior2'> payload=<property object at 0x...>>],
     'stages':
       {'stage1':
         {'a': [<default 'a' of <class 'Behavior1'> payload=True>],
          'bar': [<default 'bar' of <class 'Behavior2'> payload=<property ...
          'foo': [<default 'foo' of <class 'Behavior1'> payload=<function foo ...
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
  instruction via function call or decoration. An instruction knows the
  behavior it is declared on.

.. note:: Behaviors are created by ``behaviormetaclass``. If ``zope.interface``
  is available, it will generate ``_implements`` instructions for each behavior.
  During behavior creation the interfaces are not yet implemented, they are
  checked at a later stage. Therefore the ``_implements`` instructions are 
  generated even if the behaviors do not implement interfaces, which results in
  the empty tuple as payload (see also ``zope.interface support``.

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
    (``override`` and ``default``). Attributes declared as behavior of the
    plumbing declaration are implicit ``finalize`` declarations. Two 
    ``finalize`` for one attribute name will collide and raise a 
    ``PlumbingCollision`` during class creation.

``override``
    ``override`` is weaker than ``finalize`` and overrides declarations on base
    classes and ``default`` declarations. Two ``override`` instructions for the
    same attribute name do not collide, instead the first one will be used.

``default``
    ``default`` is the weakest extension instruction. It will not even override
    declarations of base classes. The first default takes precendence over
    later defaults.

.. contents::
    :local:


Interaction: ``finalize``, plumbing declaration and base classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In code.

.. code-block:: pycon

    >>> from plumber import finalize

    >>> class Behavior1(Behavior):
    ...     N = finalize('Behavior1')
    ...

    >>> class Behavior2(Behavior):
    ...     M = finalize('Behavior2')

    >>> class Base(object):
    ...     K = 'Base'

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(Base):
    ...     L = 'Plumbing'

    >>> for x in ['K', 'L', 'M', 'N']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Base
    L from Plumbing
    M from Behavior2
    N from Behavior1

summary:

- K-Q: attributes defined by behaviors, plumbing class and base classes
- f: ``finalize`` declaration
- x: declaration on plumbing class or base class
- ?: base class declaration is irrelevant
- **Y**: chosen end point
- collision: indicates an invalid combination, that raises a ``PlumbingCollision``

+------+-----------+-----------+----------+-------+-----------+
| Attr | Behavior1 | Behavior2 | Plumbing | Base  | ok?       |
+======+===========+===========+==========+=======+===========+
| K    |           |           |          | **x** |           |
+------+-----------+-----------+----------+-------+-----------+
| L    |           |           | **x**    | ?     |           |
+------+-----------+-----------+----------+-------+-----------+
| M    |           | **f**     |          | ?     |           |
+------+-----------+-----------+----------+-------+-----------+
| N    | **f**     |           |          | ?     |           |
+------+-----------+-----------+----------+-------+-----------+
| O    | f         |           | x        | ?     | collision |
+------+-----------+-----------+----------+-------+-----------+
| P    |           | f         | x        | ?     | collision |
+------+-----------+-----------+----------+-------+-----------+
| Q    | f         | f         |          | ?     | collision |
+------+-----------+-----------+----------+-------+-----------+

collisions.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     O = finalize(False)

    >>> @plumbing(Behavior1)
    ... class Plumbing(object):
    ...     O = True
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        Plumbing class
      with:
        <finalize 'O' of <class 'Behavior1'> payload=False>

    >>> class Behavior2(Behavior):
    ...     P = finalize(False)

    >>> @plumbing(Behavior2)
    ... class Plumbing(object):
    ...     P = True
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        Plumbing class
      with:
        <finalize 'P' of <class 'Behavior2'> payload=False>

    >>> class Behavior1(Behavior):
    ...     Q = finalize(False)

    >>> class Behavior2(Behavior):
    ...     Q = finalize(True)

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(object):
    ...     pass
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        <finalize 'Q' of <class 'Behavior1'> payload=False>
      with:
        <finalize 'Q' of <class 'Behavior2'> payload=True>


Interaction: ``override``, plumbing declaration and base classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

in code.

.. code-block:: pycon

    >>> from plumber import override

    >>> class Behavior1(Behavior):
    ...     K = override('Behavior1')
    ...     M = override('Behavior1')

    >>> class Behavior2(Behavior):
    ...     K = override('Behavior2')
    ...     L = override('Behavior2')
    ...     M = override('Behavior2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'
    ...     M = 'Base'

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(Base):
    ...     K = 'Plumbing'

    >>> for x in ['K', 'L', 'M']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Plumbing
    L from Behavior2
    M from Behavior1

summary:

- K-M: attributes defined by behaviors, plumbing class and base classes
- e: ``override`` declaration
- x: declaration on plumbing class or base class
- ?: base class declaration is irrelevant
- **Y**: chosen end point

+------+-----------+-----------+----------+------+
| Attr | Behavior1 | Behavior2 | Plumbing | Base |
+======+===========+===========+==========+======+
| K    | e         | e         | **x**    | ?    |
+------+-----------+-----------+----------+------+
| L    |           | **e**     |          | ?    |
+------+-----------+-----------+----------+------+
| M    | **e**     | e         |          | ?    |
+------+-----------+-----------+----------+------+


Interaction: ``default``, plumbing declaration and base class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

in code.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     N = default('Behavior1')

    >>> class Behavior2(Behavior):
    ...     K = default('Behavior2')
    ...     L = default('Behavior2')
    ...     M = default('Behavior2')
    ...     N = default('Behavior2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(Base):
    ...     L = 'Plumbing'

    >>> for x in ['K', 'L', 'M', 'N']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Base
    L from Plumbing
    M from Behavior2
    N from Behavior1

summary:

- K-N: attributes defined by behaviors, plumbing class and base classes
- d = ``default`` declaration
- x = declaration on plumbing class or base class
- ? = base class declaration is irrelevant
- **Y** = chosen end point

+------+-----------+-----------+----------+-------+
| Attr | Behavior1 | Behavior2 | Plumbing | Base  |
+======+===========+===========+==========+=======+
| K    |           | d         |          | **x** |
+------+-----------+-----------+----------+-------+
| L    |           | d         | **x**    | ?     |
+------+-----------+-----------+----------+-------+
| M    |           | **d**     |          |       |
+------+-----------+-----------+----------+-------+
| N    | **d**     | d         |          |       |
+------+-----------+-----------+----------+-------+


Interaction: ``finalize`` wins over ``override``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

in code.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     K = override('Behavior1')
    ...     L = finalize('Behavior1')

    >>> class Behavior2(Behavior):
    ...     K = finalize('Behavior2')
    ...     L = override('Behavior2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(Base):
    ...     pass

    >>> for x in ['K', 'L']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Behavior2
    L from Behavior1

summary:

- K-L: attributes defined by behaviors, plumbing class and base classes
- e = ``override`` declaration
- f = ``finalize`` declaration
- ? = base class declaration is irrelevant
- **Y** = chosen end point

+------+-----------+-----------+----------+------+
| Attr | Behavior1 | Behavior2 | Plumbing | Base |
+======+===========+===========+==========+======+
| K    | e         | **f**     |          | ?    |
+------+-----------+-----------+----------+------+
| L    | **f**     | e         |          | ?    |
+------+-----------+-----------+----------+------+


Interaction: ``finalize`` wins over ``default``:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

in code.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     K = default('Behavior1')
    ...     L = finalize('Behavior1')

    >>> class Behavior2(Behavior):
    ...     K = finalize('Behavior2')
    ...     L = default('Behavior2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(Base):
    ...     pass

    >>> for x in ['K', 'L']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Behavior2
    L from Behavior1

summary:

- K-L: attributes defined by behaviors, plumbing class and base classes
- d = ``default`` declaration
- f = ``finalize`` declaration
- ? = base class declaration is irrelevant
- **Y** = chosen end point

+------+-----------+-----------+----------+------+
| Attr | Behavior1 | Behavior2 | Plumbing | Base |
+======+===========+===========+==========+======+
| K    | d         | **f**     |          | ?    |
+------+-----------+-----------+----------+------+
| L    | **f**     | d         |          | ?    |
+------+-----------+-----------+----------+------+


Interaction: ``override`` wins over ``default``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

in code.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     K = default('Behavior1')
    ...     L = override('Behavior1')

    >>> class Behavior2(Behavior):
    ...     K = override('Behavior2')
    ...     L = default('Behavior2')

    >>> class Base(object):
    ...     K = 'Base'
    ...     L = 'Base'

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(Base):
    ...     pass

    >>> for x in ['K', 'L']:
    ...     print "%s from %s" % (x, getattr(Plumbing, x))
    K from Behavior2
    L from Behavior1

summary:

- K-L: attributes defined by behaviors, plumbing class and base classes
- d = ``default`` declaration
- e = ``override`` declaration
- ? = base class declaration is irrelevant
- **Y** = chosen end point

+------+-----------+-----------+----------+------+
| Attr | Behavior1 | Behavior2 | Plumbing | Base |
+======+===========+===========+==========+======+
| K    | d         | **e**     |          | ?    |
+------+-----------+-----------+----------+------+
| L    | **e**     | d         |          | ?    |
+------+-----------+-----------+----------+------+


Subclassing Behaviors
~~~~~~~~~~~~~~~~~~~~~

in code.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     J = default('Behavior1')
    ...     K = default('Behavior1')
    ...     M = override('Behavior1')

    >>> class Behavior2(Behavior1):
    ...     J = default('Behavior2') # overrides ``J`` of ``Behavior1``
    ...     L = default('Behavior2')
    ...     M = default('Behavior2') # this one wins, even if ``M`` on
    ...                              # superclass is ``override`` instruction.
    ...                              # due to ordinary inheritance behavior.

    >>> @plumbing(Behavior2)
    ... class Plumbing(object):
    ...     pass

    >>> plb = Plumbing()
    >>> plb.J
    'Behavior2'

    >>> plb.K
    'Behavior1'

    >>> plb.L
    'Behavior2'

    >>> plb.M
    'Behavior2'


Stage 2: Pipeline, docstrings and ``zope.interface`` instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In stage1 plumbing class attributes were set, which can serve as endpoints for
plumbing pipelines that are build in stage2. Plumbing pipelines correspond to
``super``-chains. Docstrings of behaviors, methods in a pipeline and properties
in a pipeline are accumulated. Plumber is ``zope.interface`` aware and takes
implemeneted interfaces from behaviors, if it can be imported.

.. contents::
    :local:


Plumbing Pipelines in general
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Elements for plumbing pipelines are declared with the ``plumb`` and
``plumbifexists`` decorators:

``plumb``
    Marks a method to be used as behavior of a plumbing pipeline.  The signature of
    such a plumbing method is ``def foo(_next, self, *args, **kw)``.  Via
    ``_next`` it is passed the next plumbing method to be called. ``self`` is
    an instance of the plumbing class, not the behavior.

``plumbifexists``
    Like ``plumb``, but only used if an endpoint exists.

The user of a plumbing class does not know which ``_next`` to pass. Therefore,
after the pipelines are built, an entrance method is generated for each pipe,
that wraps the first plumbing method passing it the correct ``_next``. Each
``_next`` method is an entrance to the rest of the pipeline.

The pipelines are build in behavior order, skipping behaviors that do not
define a pipeline element with the same attribute name::

    +---+-----------+-----------+-----------+----------+
    |   | Behavior1 | Behavior2 | Behavior3 | ENDPOINT |
    +---+-----------+-----------+-----------+----------+
    |   |      --------------------------------->      |
    | E |     x     |           |           |    x     |
    | N |      <---------------------------------      |
    + T +-----------+-----------+-----------+----------+
    | R |      ----------> --------------------->      |
    | A |     y     |     y     |           |    y     |
    | N |      <---------- <---------------------      |
    + C +-----------+-----------+-----------+----------+
    | E |           |           |      --------->      |
    | S |           |           |     z     |    z     |
    |   |           |           |      <---------      |
    +---+-----------+-----------+-----------+----------+


Method pipelines
~~~~~~~~~~~~~~~~

Two plumbing behaviors and a ``dict`` as base class. ``Behavior1`` lowercases
keys before passing them on, ``Behavior2`` multiplies results before returning
them.

.. code-block:: pycon

    >>> from plumber import plumb

    >>> class Behavior1(Behavior):
    ...     @plumb
    ...     def __getitem__(_next, self, key):
    ...         print "Behavior1 start"
    ...         key = key.lower()
    ...         ret = _next(self, key)
    ...         print "Behavior1 stop"
    ...         return ret

    >>> class Behavior2(Behavior):
    ...     @plumb
    ...     def __getitem__(_next, self, key):
    ...         print "Behavior2 start"
    ...         ret = 2 * _next(self, key)
    ...         print "Behavior2 stop"
    ...         return ret

    >>> Base = dict

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(Base):
    ...     pass

    >>> plb = Plumbing()
    >>> plb['abc'] = 6
    >>> plb['AbC']
    Behavior1 start
    Behavior2 start
    Behavior2 stop
    Behavior1 stop
    12

Plumbing pipelines need endpoints. If no endpoint is available an
``AttributeError`` is raised.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     @plumb
    ...     def foo(_next, self):
    ...         pass

    >>> @plumbing(Behavior1)
    ... class Plumbing(object):
    ...     pass
    Traceback (most recent call last):
      ...
    AttributeError: type object 'Plumbing' has no attribute 'foo'

If no endpoint is available and a behavior does not care about that,
``plumbifexists`` can be used to only plumb if an endpoint is available.

.. code-block:: pycon

    >>> from plumber import plumbifexists

    >>> class Behavior1(Behavior):
    ...     @plumbifexists
    ...     def foo(_next, self):
    ...         pass
    ...
    ...     @plumbifexists
    ...     def bar(_next, self):
    ...         return 2 * _next(self)

    >>> @plumbing(Behavior1)
    ... class Plumbing(object):
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

Plumbing of read only properties.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     @plumb
    ...     @property
    ...     def foo(_next, self):
    ...         return 2 * _next(self)

    >>> @plumbing(Behavior1)
    ... class Plumbing(object):
    ...
    ...     @property
    ...     def foo(self):
    ...         return 3

    >>> plb = Plumbing()
    >>> plb.foo
    6

It is possible to extend a property with so far unset getter/setter/deleter.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     @plumb
    ...     @property
    ...     def foo(_next, self):
    ...         return 2 * _next(self)

    >>> class Behavior2(Behavior):
    ...     def set_foo(self, value):
    ...         self._foo = value
    ...     foo = plumb(property(
    ...         None,
    ...         override(set_foo),
    ...         ))

    >>> @plumbing(Behavior1, Behavior2)
    ... class Plumbing(object):
    ...
    ...     @property
    ...     def foo(self):
    ...         return self._foo

    >>> plb = Plumbing()
    >>> plb.foo = 4
    >>> plb.foo
    8


Subclassing Behaviors
~~~~~~~~~~~~~~~~~~~~~

Other than stage 1 instructions, which extend a class with properties
and functions and thus override each other by the rules of ordinary
subclassing, pipeline instructions are aggregated.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ... 
    ...     @plumb
    ...     def foo(_next, self):
    ...         return 'Behavior1 ' + _next(self)
    ... 
    ...     @plumb
    ...     def bar(_next, self):
    ...         return 'Behavior1 ' + _next(self)

    >>> class Behavior2(Behavior1):
    ... 
    ...     @plumb
    ...     def foo(_next, self):
    ...         return 'Behavior2 ' + _next(self)

    >>> @plumbing(Behavior2)
    ... class Plumbing(object):
    ... 
    ...     def foo(self):
    ...         return 'foo'
    ... 
    ...     def bar(self):
    ...         return 'bar'

    >>> plb = Plumbing()
    >>> plb.foo()
    'Behavior2 Behavior1 foo'
    
    >>> plb.bar()
    'Behavior1 bar'


Mixing methods and properties within the same pipeline is not possible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Within a pipeline all elements need to be of the same type, it is not possible
to mix properties with methods.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     @plumb
    ...     def foo(_next, self):
    ...         return _next(self)

    >>> @plumbing(Behavior1)
    ... class Plumbing(object):
    ...
    ...     @property
    ...     def foo(self):
    ...         return 5
    Traceback (most recent call last):
      ...
    PlumbingCollision:
        <plumb 'foo' of <class 'Behavior1'> payload=<function foo at 0x...>>
      with:
        <class 'Plumbing'>


docstrings of classes, methods and properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Normal docstrings of the plumbing declaration and the behavior classes, plumbed
methods and plumbed properties are joined by newlines starting with the
plumbing declaration and followed by the behaviors in reverse order.

.. code-block:: pycon

    >>> class P1(Behavior):
    ...     """P1
    ...     """
    ...     @plumb
    ...     def foo(self):
    ...         """P1.foo
    ...         """
    ...     bar = plumb(property(None, None, None, "P1.bar"))

    >>> class P2(Behavior):
    ...     @override
    ...     def foo(self):
    ...         """P2.foo
    ...         """
    ...     bar = plumb(property(None, None, None, "P2.bar"))

    >>> @plumbing(P1, P2)
    ... class Plumbing(object):
    ...     """Plumbing
    ...     """
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


Slots and plumbings
~~~~~~~~~~~~~~~~~~~

A plumbing class can have __slots__ like normal classes.

.. code-block:: pycon

    >>> class P1(Behavior):
    ...     @default
    ...     def somewhing_which_writes_to_foo(self, foo_val):
    ...         self.foo = foo_val

    >>> @plumbing(P1)
    ... class WithSlots(object):
    ...     __slots__ = 'foo'

    >>> WithSlots.__dict__['foo']
    <member 'foo' of 'WithSlots' objects>

    >>> ob = WithSlots()
    >>> ob.somewhing_which_writes_to_foo('foo')
    >>> assert(ob.foo == 'foo')


``zope.interface`` (if available)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plumber does not depend on ``zope.interface`` but is aware of it. That
means it will try to import it and if available will check plumbing behaviors
for implemented interfaces and will make the plumbing implement them, too.

.. code-block:: pycon

    >>> from zope.interface import Interface
    >>> from zope.interface import implementer

A class with an interface that will serve as base class of a plumbing.

.. code-block:: pycon

    >>> class IBase(Interface):
    ...     pass

    >>> @implementer(IBase)
    ... class Base(object):
    ...     pass

    >>> IBase.implementedBy(Base)
    True

Two behaviors with corresponding interfaces, one with a base class that also
implements an interface.

.. code-block:: pycon

    >>> class IBehavior1(Interface):
    ...     pass

    >>> @implementer(IBehavior1)
    ... class Behavior1(Behavior):
    ...     blub = 1

    >>> class IBehavior2Base(Interface):
    ...     pass

    >>> @implementer(IBehavior2Base)
    ... class Behavior2Base(Behavior):
    ...     pass

    >>> class IBehavior2(Interface):
    ...     pass

    >>> @implementer(IBehavior2)
    ... class Behavior2(Behavior2Base):
    ...     pass

    >>> IBehavior1.implementedBy(Behavior1)
    True

    >>> IBehavior2Base.implementedBy(Behavior2Base)
    True

    >>> IBehavior2Base.implementedBy(Behavior2)
    True

    >>> IBehavior2.implementedBy(Behavior2)
    True

A plumbing based on ``Base`` using ``Behavior1`` and ``Behavior2`` and
implementing ``IPlumbingClass``.

.. code-block:: pycon

    >>> class IPlumbingClass(Interface):
    ...     pass

    >>> @implementer(IPlumbingClass)
    ... @plumbing(Behavior1, Behavior2)
    ... class PlumbingClass(Base):
    ...     pass

The directly declared and inherited interfaces are implemented.

.. code-block:: pycon

    >>> IPlumbingClass.implementedBy(PlumbingClass)
    True

    >>> IBase.implementedBy(PlumbingClass)
    True

The interfaces implemented by the Behaviors are also implemented.

.. code-block:: pycon

    >>> IBehavior1.implementedBy(PlumbingClass)
    True

    >>> IBehavior2.implementedBy(PlumbingClass)
    True

    >>> IBehavior2Base.implementedBy(PlumbingClass)
    True

An instance of the class provides the interfaces.

.. code-block:: pycon

    >>> plumbing = PlumbingClass()

    >>> IPlumbingClass.providedBy(plumbing)
    True

    >>> IBase.providedBy(plumbing)
    True

    >>> IBehavior1.providedBy(plumbing)
    True

    >>> IBehavior2.providedBy(plumbing)
    True

    >>> IBehavior2Base.providedBy(plumbing)
    True


Miscellanea
-----------

Nomenclature
^^^^^^^^^^^^

**``plumber``**
    Metaclass that creates a plumbing according to the instructions declared on
    plumbing behaviors. Instructions are given by decorators: ``default``,
    ``override``, ``finalize``, ``plumb`` and ``plumbifexists``.

**plumbing**
    A plumbing is a class decorated by ``plumbing`` decorator which gets passed
    the behviors to apply, e.g. ``@plumbing(Behavior1, Behavior2)``. Apart from
    the behaviors, declarations on base classes and the class asking for the
    plumber are taken into account. Once created, a plumbing looks like any
    other class and can be subclassed as usual.

**plumbing behavior**
    A plumbing behavior provides attributes (functions, properties and plain
    values) along with instructions for how to use them. Instructions are given
    via decorators: ``default``, ``override``, ``finalize``, ``plumb`` and
    ``plumbifexists`` (see Stage 1:... and Stage 2:...).

**plumbing pipeline**
    Plumbing methods/properties with the same name form a pipeline. The
    entrance and end-point have the signature of normal methods: ``def
    foo(self, *args, **kw)``. The plumbing pipelines is a series of nested
    closures (see ``_next``).

**entrance (method)**
    A method with a normal signature. i.e. expecting ``self`` as first
    argument, that is used to enter a pipeline. It is a ``_next`` function. A
    method declared on the class with the same name, will be overwritten, but
    referenced in the pipelines as the innermost method, the endpoint.

**``_next`` function**
    The ``_next`` function is used to call the next method in a pipelines: in
    case of a plumbing method, it is a wrapper of it that passes the correct
    next ``_next`` as first argument and in case of an end-point, just the
    end-point method itself.

**end-point (method)**
    Method retrieved from the plumbing class with ``getattr()``, before setting
    the entrance method on the class.

If you feel something is missing, please let us now or write a short
corresponding text.


Test Coverage
^^^^^^^^^^^^^

.. image:: https://travis-ci.org/bluedynamics/plumber.svg?branch=master
    :target: https://travis-ci.org/bluedynamics/plumber

Coverage report::

    Name                                      Stmts   Miss  Cover
    -------------------------------------------------------------
    src/plumber/__init__.py                      10      0   100%
    src/plumber/behavior.py                      49      0   100%
    src/plumber/compat.py                         9      0   100%
    src/plumber/exceptions.py                     6      0   100%
    src/plumber/instructions.py                 172      0   100%
    src/plumber/plumber.py                       71      0   100%
    src/plumber/tests/__init__.py               574      0   100%
    src/plumber/tests/globalmetaclass.py         15      0   100%
    -------------------------------------------------------------
    TOTAL                                      1882      0   100%


Python Versions
^^^^^^^^^^^^^^^

- Python 2.6+, 3.3+, pypy

- May work with other versions (untested)


Contributors
^^^^^^^^^^^^

- Florian Friesdorf

- Robert Niederreiter

- Jens W. Klein

- Marco Lempen

- Attila Oláh


Changes
^^^^^^^

1.4
---

- No more "private" module names.
  [rnix, 2017-05-21]

- Python 3 support.
  [rnix, 2017-05-18]


1.3.1
-----

- Avoid use of deprecated ``dict.has_key``.
  [rnix, 2015-10-05]


1.3
---

- Introduce ``plumbing`` decorator.
  [rnix, 2014-07-31]

- Remove deprecated ``plumber.extend`` and ``plumber.Part``.
  [rnix, 2014-07-31]


1.2
---

- Deprecate ``plumber.extend``. Use ``plumber.override`` instead.
  [rnix, 2012-07-28]

- Deprecate ``plumber.Part``. Use ``plumber.Behavior`` instead.
  [rnix, 2012-07-28]


1.1
---

- Use ``zope.interface.implementer`` instead of ``zope.interface.implements``.
  [rnix, 2012-05-18]


1.0
---

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


License / Disclaimer
^^^^^^^^^^^^^^^^^^^^

Copyright (c) 2011-2017, BlueDynamics Alliance, Austria, Germany, Switzerland
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
