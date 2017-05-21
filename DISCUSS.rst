Design choices and ongoing discussions
======================================

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
