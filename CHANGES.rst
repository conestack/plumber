Changes
=======

3.0.0 (unreleased)
------------------

- Build plumbing pipelines once at class creation time instead of creating
  closures and joining docstrings on every call. Each ``next_`` is a
  ``functools.partial`` now. Calling a method plumbed by 5 behaviors takes
  about a tenth of the time.
  [rnix]

- Tracebacks show the plumbing class and behaviors: the entrance frame reads
  ``Plumbing.foo [Behavior1 -> Behavior2]``, plumbing method frames read
  ``Behavior1.foo [plumbing Plumbing]``. pytest hides the entrance frame.
  Entrance methods get ``__qualname__`` and ``__module__`` of the plumbing
  class.
  [rnix]

- Plumb property accessors independently. Behaviors not defining an accessor
  are skipped instead of failing at class creation.
  [rnix]


2.0.1 (2026-10-31)
------------------

- Modernise the code ruff flags as outdated: ``class X(object)``. Behaviour
  unchanged. ``super(Class, self)`` is kept, see ``cone.app``.
  [rnix]

- Sort the imports with ruff (one per line, ``from`` imports first, no
  sections) and format the code with ``ruff format`` (90 characters per line,
  single quotes).
  [rnix]

- Pin the ruff configuration in ``pyproject.toml``: rule selection, import
  sorting and formatter settings, ``make check`` runs ``ruff check`` with it.
  [rnix]


2.0.0 (2026-02-03)
------------------

- Refactor package layout to use ``pyproject.toml``.
  [rnix]

- Drop Python 2 support.
  [rnix]


1.7 (2022-03-17)
----------------

- Do not run test suites for Python 2.6 and Python < 3.7 any more.
  [rnix, 2022-03-16]

- Replace ``Bases`` wrapper with a ``set`` containing ``derived_members``
  to avoid multiple base class iteration.
  [rnix, 2022-02-13]

- Only keep most recent instructions on ``Stacks`` when parsing behaviors.
  [rnix, 2022-02-13]

- Simplify ``Stacks`` object.
  [rnix, 2022-02-13]

- Apply stage 1 and stage 2 instructions in ``plumber.__new__`` instead of
  applying stage 2 instructions in ``plumber.__init__``.
  [rnix, 2022-02-13]


1.6
---

- Use raw string for regular expression.
  [rnix, 2020-05-28]

- Drop python 2.6 support.
  [rnix, 2019-03-25]


1.5
---

- Introduce ``plumber.metaclasshook`` decorator.
  [rnix, 2017-06-16]


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
