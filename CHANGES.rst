Changes
=======

1.7 (unreleased)
----------------

- Add abstract base class support.
  [rnix, 2022-01-28]


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
