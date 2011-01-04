=======
Plumber
=======

A plumber is a metaclass that implements a plumbing system which works
orthogonal to subclassing.

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

The last method, the end point or exit of a pipeline is under discussion.


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

Global imports
~~~~~~~~~~~~~~
XXX: Bases is experimental, well, even more than the rest.
::

    >>> from plumber._plumber import Bases

Import of the plumbing decorator for the plumbing methods and the Plumber
metaclass.
::

    >>> from plumber import plumbing
    >>> from plumber import Plumber


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

    >>> class NotifyDict(dict):
    ...     """A dictionary that prints notification on __setitem__
    ...     """
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Notifier, dict)

    >>> ndict = NotifyDict(notify=True)
    <class 'Notifier'>.__init__: begin with: <NotifyDict object at ...>.
    <class 'Notifier'>.__init__: end.

The paremeter set by the plumbing __init__ made it onto the created object.
::

    >>> ndict.notify
    True

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

XXX: In __init__ we can put additional attributes onto a pipelined object.
Should it be possible to add new methods? or do we want a subclass of the
pipelined object in order to achieve that? Currently all methods of the
plumbing needs one end point on the final plumbing element (also inherited is
possible) and it is not possible to use a plumbing element to add normal
methods. In the above example it would not be possible for a subclass of
NotifyPrefixDict to override the prefix and unprefix methods as they are not
in NotifyPrefixDict's MRO but are defined on the plumbing element and called
via plumbing methods. It feels, that for such purposes no classmethods on the
plumbing element should be used, but that the plumbing element is able to put
new methods on the class.

As a plumbing element cannot know whether other elements defined methods with
the same name, it needs to stick to plumbing methods with calls to _next. It is
the job of the plumber to figure out what to do, in case there is no method
defined in the end point. In that case a special _next method could be passed
which raises NotImplemented and a plumbing element that knows what it is doing
(e.g. above with prefix and unprefix) would just not call _next.

    >>> class NotifyPrefixDict(dict):
    ...     """A dictionary that prints notifications and has prefixed keys
    ...     """
    ...     __metaclass__ = Plumber
    ...     __pipeline__ = (Notifier, Prefixer, dict)

XXX: This collides with dict __init__ signature: dict(foo=1, bar=2)
--> creating a subclass of dict that does __init__ translation might work:
data=() - eventually a specialized plugin, but let's keep this simple for now.

XXX: If __init__ would be defined here, when would that happen? Can you use
super in __init__ and what is called by it?

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
    ...     __pipeline__ = (Prefixer, Notifier, Bases)

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

What about defining code in the new class that is sitting in front of the
plumbing. It could also mean that the code defined here is sitting behind the
plumbing.

#    >>> class Foo(dict):
#    ...     __metaclass__ = Plumber
#    ...     __pipeline__ = (Notifier, dict)
#    ...
#    ...     def __init__(self, foo=True):
#    ...         super(Foo, self).__init__()
#    ...         self.foo = foo

Two possibilites:
1. explicit subclassing:

#   >>> class FooPlumbing(dict):
#   ...     __metaclass__ = Plumber
#   ...     __pipeline__ = (Notifier, dict)
#
#   >>> class Foo(FooPlumbing):
#    ...     def __init__(self, foo=True):
#    ...         super(Foo, self).__init__()
#    ...         self.foo = foo

2. flag for implicit creation of the plumbing and implicit subclassing of it

Currently the exit point is defined by the last plugin in the pipeline.
Normally one would just want to use normal inheritance resolution. However,
this normal behaviour should also be explicitly defined.

What can code defined in the plumbing class mean?

@plumbing methods would be treated as in front of the plumbing

normal methods instead are treated as behind the plumbing but in front of the
bases

Lets see this in action before thinking to much about it.


Subclassing
===========

Subclass of a class that uses a plumber
---------------------------------------

Subclassing a class that uses a plumber is working normally. Without a call to
super, the inherited method is just overwritten.
::

    >>> class SubNotifyDict(PrefixNotifyDict):
    ...     def __init__(self):
    ...         print "SubNotifier.__init__ is called."

    >>> snd = SubNotifyDict()
    SubNotifier.__init__ is called.

And with a call to super the plumbing methods will be called.
::

    >>> class SubNotifyDict(PrefixNotifyDict):
    ...     def __init__(self):
    ...         print "SubNotifier.__init__ is called."
    ...         super(SubNotifyDict, self).__init__(notify=True)
    ...         print "SubNotifier.__init__ finishes."

    >>> snd = SubNotifyDict()
    SubNotifier.__init__ is called.
    <class 'Prefixer'>.__init__: begin with: <SubNotifyDict object at ...>.
    <class 'Notifier'>.__init__: begin with: <SubNotifyDict object at ...>.
    <class 'Notifier'>.__init__: end.
    <class 'Prefixer'>.__init__: end.
    SubNotifier.__init__ finishes.

The Plumber metaclass achieves this behaviour by only working on classes that
declare ``__metaclass__ = Plumber`` themselves, i.e. it is in their
``cls.__dict__``. The plumber will be called to create ``SubNotifyDict`` as
``SubNotifyDict`` inherits the ``__metaclass__`` declaration from
``PrefixNotifyDict``, but the plumber will just leave the job to ``type``.



Multiple inheritance and plumbers all over
------------------------------------------



Subclassing plumbing elements
-----------------------------



Discussions
===========

Where is the plumbing
---------------------

It would/could also be possible to use a plumbing for a class without base
clases. That would mean that the code defined on the class that uses plumbing
is sitting behind the plumbing and as usual in front of the base clases.

Now is it better to be able to use plumbing for a class that has no bases or
more likely that one wants to define code on the class that uses plumbing which
is meant to be sitting in front of the plumbing.

We could made this explicitly configurable by putting Self as a special
__pipeline__ element, valid at the very beginning or at the end. To enable it
at the beginning we probably need to create another class that uses the
plumbing which will be put between the bases and the newly created class.


Signature of _next function
---------------------------

Currently ``self`` needs to be passed to the ``_next`` function. This could be
wrapped, too. However, it might enable cool stuff, because you can decide to
pass something else than self to be processed further.



Instances of plumbing elements
------------------------------

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

Last but not least, in case we decide to prefix all plumbing methods, this can
be introduced while being backwards compatible with the current setup.
Therefore, I suggest to gather experience with the current approach first.


Implicit subclass generation
----------------------------

Currently the whole plumbing system is implemented within one class that is
based on the base classes defined in the class declaration. During class
creation the plumber determines all functions involved in the plumbing,
generates pipelines of methods and plumbs them together.

An alternative approach would be to take one plumbing elements after another
and create a subclass chain. However, I currently don't know how this could be
achieved, believe that it is not possible and think that the current approach
is better.


Positional arguments
--------------------

Currently, it is not possible to pass positional arguments ``*args`` to
plumbing methods and therefore everything behind the plumbing system. In
python, this syntax is not valid ``def f(foo, *args, bar=1, **kws)``. If you
have any idea how to support positional arguments, pleas let us know.



Contributors
============

- Florian Friesdorf <flo@chaoflow.net>
- Robert Niederreiter <rnix@squarewave.at>
- Attila Oláh
- WSGI


Changes
=======

- initial [chaoflow, 2011-01-04]


TODO
====

...
