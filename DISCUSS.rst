Design choices and ongoing discussions
======================================

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
