TODO
----

- [ ] mature plumbing of properties.

- [ ] keep ``__qualname__`` of classes decorated with ``plumbing``. The
  decorator recreates the class from ``cls.__dict__``, which does not contain
  ``__qualname__``, so it falls back to ``__name__``. This only affects classes
  defined inside other classes or functions: their ``repr`` is wrong and their
  instances can not be pickled. Fixing it changes the ``repr`` of such classes,
  ``node`` tests compare it and need to be adapted first.
