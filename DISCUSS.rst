Design choices and ongoing discussions
======================================

Inherit plumber and behavior metaclasses from abc.ABCMeta
---------------------------------------------------------

Currently specific plumber and behavior metaclasses are provided for abc
support. It is the most widely used "build-in" metaclass in the standard lib.


Pros
~~~~

- Metaclasses cannot be mixed by default, so we won't break anything but simply
  gain support for ABC.

- Straight forward implementation.

- No dedicated ``ABCBehavior`` base implementation required.

- No validation hook for plumbing classes using ``ABCBehavior`` required.


Cons
~~~~

- Creating other custom plumber metaclasses gets more difficult and error prone
  because of ABC behavior is present in base metaclasses.


Usage of metaclasses in the standard lib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below a grep over python 3.7's lib directory.

.. code-block:: sh

  /usr/lib/python3.7$ grep -rnI 'metaclass='
  _pyio.py:281:class IOBase(metaclass=abc.ABCMeta):
  multiprocessing/reduction.py:247:class AbstractReducer(metaclass=ABCMeta):
  ctypes/_endian.py:46:    class BigEndianStructure(Structure, metaclass=_swapped_meta):
  ctypes/_endian.py:55:    class LittleEndianStructure(Structure, metaclass=_swapped_meta):
  _collections_abc.py:84:class Hashable(metaclass=ABCMeta):
  _collections_abc.py:99:class Awaitable(metaclass=ABCMeta):
  _collections_abc.py:158:class AsyncIterable(metaclass=ABCMeta):
  _collections_abc.py:243:class Iterable(metaclass=ABCMeta):
  _collections_abc.py:359:class Sized(metaclass=ABCMeta):
  _collections_abc.py:374:class Container(metaclass=ABCMeta):
  _collections_abc.py:398:class Callable(metaclass=ABCMeta):
  typing.py:1156:class _Protocol(Generic, metaclass=_ProtocolMeta):
  typing.py:1377:class NamedTuple(metaclass=NamedTupleMeta):
  lib2to3/fixes/fix_metaclass.py:1:"""Fixer for __metaclass__ = X -> (metaclass=X) methods.
  lib2to3/fixes/fix_metaclass.py:203:        # compact the expression "metaclass = Meta" -> "metaclass=Meta"
  pydoc_data/topics.py:8757:                 '   class MyClass(metaclass=Meta):\n'
  pydoc_data/topics.py:9615:                 '   >>> class C(object, metaclass=Meta):\n'
  string.py:78:class Template(metaclass=_TemplateMetaclass):
  selectors.py:80:class BaseSelector(metaclass=ABCMeta):
  abc.py:18:        class C(metaclass=ABCMeta):
  abc.py:34:        class C(metaclass=ABCMeta):
  abc.py:57:        class C(metaclass=ABCMeta):
  abc.py:84:        class C(metaclass=ABCMeta):
  abc.py:92:        class C(metaclass=ABCMeta):
  abc.py:166:class ABC(metaclass=ABCMeta):
  enum.py:520:class Enum(metaclass=EnumMeta):
  importlib/abc.py:30:class Finder(metaclass=abc.ABCMeta):
  importlib/abc.py:136:class Loader(metaclass=abc.ABCMeta):
  importlib/abc.py:345:class ResourceReader(metaclass=abc.ABCMeta):
  io.py:72:class IOBase(_io._IOBase, metaclass=abc.ABCMeta):
  numbers.py:12:class Number(metaclass=ABCMeta):
  dataclasses.py:206:class InitVar(metaclass=_InitVarMeta):
  email/_policybase.py:112:class Policy(_PolicyBase, metaclass=abc.ABCMeta):


Stage1 left of stage2
---------------------

Currently instructions of stage1 may be left of stage2 instructions. We
consider to forbid this.

.. code-block:: pycon

    >>> class Behavior1(Behavior):
    ...     @override
    ...     def foo(self):
    ...         return 5

    >>> class Behavior2(Behavior):
    ...     @plumb
    ...     def foo(_next, self):
    ...         return 2 * _next(self)

    >>> class Plumbing(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = Behavior1, Behavior2

    >>> Plumbing().foo()
    10

- [rnix, 2012-07-29]: I still see no advantage in forbidding to define an
  endpoint on the left of a plumbing to the same. It's different semantics.


Instance based plumbing system
------------------------------

At various points it felt tempting to be able to instantiate plumbing elements
to configure them. For that we need ``__init__``, which would mean that plumbing
``__init__`` would need a different name, eg. ``prt_``-prefix. Consequently
this would then be done for all plumbing methods.

Reasoning why currently the methods are not prefixed:
Plumbing elements are simply not meant to be normal classes. Their methods have
the single purpose to be called as behavior of some other class' method calls,
never directly. Configuration of plumbing elements can either be achieved by
subclassing them or by putting the configuration on the objects/class they are
used for.

- [rnix, 2012-07-29]: It turned out that providing necessary plumbing behavior
  configuration via plumbed classes is quite handy and readable. I would
  suggest to stick to this strategy.

An instance based plumbing system would be far more complex. It could be
implemented to exist alongside the current system.


Different zope.interface.Interfaces for plumbing and created class
------------------------------------------------------------------

A different approach to the currently implemented system is having different
interfaces for the behaviors and the class that is created.

.. code-block:: pycon

    >>> class IBehavior1Behaviour(Interface):
    ...     pass

    >>> @implementer(IBehavior1)
    ... class Behavior1(Behavior):
    ...     interfaces = (IBehavior1Behaviour,)

    >>> class IBehavior2(Interface):
    ...     pass

    >>> @implementer(IBehavior2)
    ... class Behavior2(Behavior):
    ...     interfaces = (IBehavior2Behaviour,)

    >>> IUs.implementedBy(Us)
    True
    
    >>> IBase.implementedBy(Us)
    True
    
    >>> IBehavior1.implementedBy(Us)
    False
    
    >>> IBehavior2.implementedBy(Us)
    False
    
    >>> IBehavior1Behaviour.implementedBy(Us)
    False
    
    >>> IBehavior2Behaviour.implementedBy(Us)
    False

Same reasoning as before: up to now unnecessary complexity. It could make sense
in combination with an instance based plumbing system and could be implemented
as behavior of it alongside the current class based system.

- [rnix, 2012-07-29]: One of the advantages of interfaces is to ask whether an
  object instanciates it. By applying a behavior implementing some interface to
  a class this class indeed implements this interface. For later instance based
  plumbing ``zope.interface.alsoProvides`` can be used in order to keep things
  sane.
