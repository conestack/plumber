from plumber import Behavior
from plumber import PlumbingCollision
from plumber import default
from plumber import finalize
from plumber import override
from plumber import plumb
from plumber import plumber
from plumber import plumbifexists
from plumber import plumbing
from plumber.behavior import behaviormetaclass
from plumber.compat import add_metaclass
from plumber.instructions import Instruction
from plumber.instructions import _implements
from plumber.instructions import payload
from plumber.instructions import plumb_str
from plumber.plumber import searchnameinbases
from zope.interface import Interface
from zope.interface import implementer
from zope.interface.interface import InterfaceClass
import inspect
import sys


if sys.version_info < (2, 7):                                # pragma: no cover
    import unittest2 as unittest
else:                                                        # pragma: no cover
    import unittest


class TestInstructions(unittest.TestCase):

    def test_payload(self):
        class Foo:
            pass

        self.assertTrue(payload(Instruction(Instruction(Foo))) is Foo)

    def test_plumb_str(self):
        leftdoc = """Left head

        __plbnext__

        Left tail
        """
        rightdoc = """Right head

        __plbnext__

        Right tail
        """
        self.assertEqual(plumb_str(leftdoc, rightdoc).split('\n'), [
            'Left head',
            '',
            '        Right head',
            '',
            '        __plbnext__',
            '',
            '        Right tail',
            '',
            '        Left tail',
            '        '
        ])
        leftdoc = """Left tail
        """
        rightdoc = """Right tail
        """
        self.assertEqual(plumb_str(leftdoc, rightdoc).split('\n'), [
            'Right tail',
            '',
            'Left tail',
            '        '
        ])

        class A:
            pass

        self.assertTrue(plumb_str(A, None) is A)
        self.assertTrue(plumb_str(None, A) is A)
        self.assertTrue(plumb_str(None, None) is None)

    def test_instruction(self):
        class Foo:
            pass

        self.assertTrue(Instruction(Foo).item is Foo)
        self.assertTrue(Instruction(Foo).__name__ is None)
        self.assertTrue(Instruction(Foo, name='foo').__name__ == 'foo')
        self.assertRaises(
            NotImplementedError,
            lambda: Instruction(None) + 1
        )
        self.assertRaises(
            NotImplementedError,
            lambda: Instruction(None)(None)
        )

    def test_default(self):
        # First default wins from left to right
        def1 = default(1)
        self.assertTrue(def1 + def1 is def1)
        def2 = default(2)
        self.assertTrue(def1 + def2 is def1)
        self.assertTrue(def2 + def1 is def2)
        # Override wins over default
        ext3 = override(3)
        self.assertTrue(def1 + ext3 is ext3)
        # Finalize wins over default
        fin4 = finalize(4)
        self.assertTrue(def1 + fin4 is fin4)
        # Adding with something else than default/override, raises
        # ``PlumbingCollision``
        err = None
        try:
            def1 + Instruction('foo')
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__class__.__name__, 'default')
            self.assertEqual(err.left.payload, 1)
            self.assertEqual(err.right.__class__.__name__, 'Instruction')
            self.assertEqual(err.right.payload, 'foo')

    def test_override(self):
        # First override wins against following equal overrides and arbitrary
        # defaults
        ext1 = override(1)
        self.assertTrue(ext1 + ext1 is ext1)
        self.assertTrue(ext1 + override(1) is ext1)
        self.assertTrue(ext1 + override(2) is ext1)
        self.assertTrue(ext1 + default(2) is ext1)
        fin3 = finalize(3)
        self.assertTrue(ext1 + fin3 is fin3)
        # Everything except default/override collides
        err = None
        try:
            ext1 + Instruction(1)
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__class__.__name__, 'override')
            self.assertEqual(err.left.payload, 1)
            self.assertEqual(err.right.__class__.__name__, 'Instruction')
            self.assertEqual(err.right.payload, 1)

    def test_finalize(self):
        # First override wins against following equal overrides and arbitrary
        # defaults
        fin1 = finalize(1)
        self.assertTrue(fin1 + fin1 is fin1)
        self.assertTrue(fin1 + finalize(1) is fin1)
        self.assertTrue(fin1 + default(2) is fin1)
        self.assertTrue(fin1 + override(2) is fin1)
        # Two unequal finalize collide
        err = None
        try:
            fin1 + finalize(2)
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__class__.__name__, 'finalize')
            self.assertEqual(err.left.payload, 1)
            self.assertEqual(err.right.__class__.__name__, 'finalize')
            self.assertEqual(err.right.payload, 2)
        # Everything except default/override collides
        try:
            fin1 + Instruction(1)
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__class__.__name__, 'finalize')
            self.assertEqual(err.left.payload, 1)
            self.assertEqual(err.right.__class__.__name__, 'Instruction')
            self.assertEqual(err.right.payload, 1)

    def test_plumb(self):
        plb1 = plumb(1)
        self.assertTrue(plb1 + plumb(1) is plb1)
        err = None
        try:
            plb1 + Instruction(1)
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__class__.__name__, 'plumb')
            self.assertEqual(err.left.payload, 1)
            self.assertEqual(err.right.__class__.__name__, 'Instruction')
            self.assertEqual(err.right.payload, 1)
        try:
            func_a = lambda x: None
            prop_b = property(lambda x: None)
            plumb(func_a) + plumb(prop_b)
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__class__.__name__, 'plumb')
            self.assertEqual(err.left.payload, func_a)
            self.assertEqual(err.right.__class__.__name__, 'plumb')
            self.assertEqual(err.right.payload, prop_b)
        try:
            plumb(1) + plumb(2)
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__class__.__name__, 'plumb')
            self.assertEqual(err.left.payload, 1)
            self.assertEqual(err.right.__class__.__name__, 'plumb')
            self.assertEqual(err.right.payload, 2)

    def test_implements(self):
        # classImplements interfaces
        foo = _implements(('foo',))
        self.assertTrue(foo == foo)
        self.assertTrue(foo + foo is foo)
        self.assertTrue(foo == _implements(('foo',)))
        self.assertTrue(foo != _implements(('bar',)))
        self.assertTrue(
            _implements(('foo', 'bar')) == _implements(('bar', 'foo'))
        )
        self.assertTrue(foo + _implements(('foo',)) is foo)
        bar = _implements(('bar',))
        foobar = foo + bar
        self.assertEqual(foobar.__class__.__name__, '_implements')
        self.assertEqual(foobar.__name__, '__interfaces__')
        self.assertEqual(foobar.payload, ('bar', 'foo'))
        self.assertTrue(foo + bar == bar + foo)
        err = None
        try:
            foo + Instruction("bar")
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__class__.__name__, '_implements')
            self.assertEqual(err.left.__name__, '__interfaces__')
            self.assertEqual(err.left.payload, ('foo',))
            self.assertEqual(err.right.__class__.__name__, 'Instruction')
            self.assertEqual(err.right.payload, 'bar')


class TestBehavior(unittest.TestCase):

    def test_behaviormetaclass(self):
        @add_metaclass(behaviormetaclass)
        class A(object):
            pass

        self.assertEqual(
            getattr(A, '__plumbing_instructions__', 'No behavior'),
            'No behavior'
        )

        @add_metaclass(behaviormetaclass)
        class B(Behavior):
            pass

        self.assertEqual(
            getattr(B, '__plumbing_instructions__', None) and 'Behavior',
            'Behavior'
        )


class TestPlumber(unittest.TestCase):

    def test_searchnameinbases(self):
        class A(object):
            foo = 1

        class B(A):
            pass

        self.assertTrue(searchnameinbases('foo', (B,)))
        self.assertFalse(searchnameinbases('bar', (B,)))


class TestGlobalMetaclass(unittest.TestCase):

    @unittest.skipIf(
        sys.version_info[0] >= 3,
        '__metaclass__ attribute on module leven only works in python 2')
    def test_global_metaclass(self):
        from plumber.tests import globalmetaclass as gm
        # A zope.interface.Interface is not affected by the global
        # ``__metaclass__``.
        self.assertEqual(gm.IBehavior1.__class__, InterfaceClass)

        # A global meta-class declaration makes all classes at least new-style
        # classes, even when not subclassing subclasses
        self.assertEqual(gm.Foo.__class__, plumber)
        self.assertTrue(issubclass(gm.Foo, object))

        # If subclassing object, the global metaclass declaration is ignored::
        self.assertEqual(gm.ClassMaybeUsingAPlumbing.__class__, type)

        self.assertEqual(gm.ClassReallyUsingAPlumbing.__class__, plumber)
        self.assertTrue(issubclass(gm.ClassReallyUsingAPlumbing, object))
        self.assertTrue(
            gm.IBehavior1.implementedBy(gm.ClassReallyUsingAPlumbing)
        )

        self.assertEqual(gm.BCClassReallyUsingAPlumbing.__class__, plumber)
        self.assertTrue(issubclass(gm.BCClassReallyUsingAPlumbing, object))
        self.assertTrue(
            gm.IBehavior1.implementedBy(gm.BCClassReallyUsingAPlumbing)
        )


class TestMetaclassHooks(unittest.TestCase):

    def test_metaclasshook(self):
        class IBehaviorInterface(Interface):
            pass

        @plumber.metaclasshook
        def test_metclass_hook(cls, name, bases, dct):
            if not IBehaviorInterface.implementedBy(cls):
                return
            cls.hooked = True

        self.assertTrue(test_metclass_hook in plumber.__metaclass_hooks__)

        @implementer(IBehaviorInterface)
        class MetaclassConsideredBehavior(Behavior):
            pass

        @plumbing(MetaclassConsideredBehavior)
        class Plumbing(object):
            pass

        self.assertTrue(Plumbing.hooked)

        class BehaviorIgnoredByMetaclassHook(Behavior):
            pass

        @plumbing(BehaviorIgnoredByMetaclassHook)
        class Plumbing2(object):
            pass

        self.assertRaises(AttributeError, lambda: Plumbing2.hooked)

        plumber.__metaclass_hooks__.remove(test_metclass_hook)


class TestPlumberBasics(unittest.TestCase):

    def test_basics(self):
        class Behavior1(Behavior):
            a = default(True)

            @default
            def foo(self):
                return 42

        class Behavior2(Behavior):
            @default
            @property
            def bar(self):
                return 17

        Base = dict

        @plumbing(Behavior1, Behavior2)
        class Plumbing(Base):

            def foobar(self):
                return 5

        plb = Plumbing()
        self.assertTrue(plb.a)
        self.assertEqual(plb.foo(), 42)
        self.assertEqual(plb.bar, 17)
        self.assertEqual(plb.foobar(), 5)
        plb['a'] = 1
        self.assertEqual(plb['a'], 1)

        class Sub(Plumbing):
            a = 'Sub'

        self.assertEqual(Sub.a, 'Sub')
        self.assertEqual(Sub().foo(), 42)
        self.assertEqual(Sub().bar, 17)
        self.assertEqual(Sub().foobar(), 5)

        stacks = Plumbing.__plumbing_stacks__
        self.assertEqual(len(stacks['history']), 5)
        stages = stacks['stages']
        self.assertEqual(sorted(list(stages.keys())), ['stage1', 'stage2'])
        stage_1 = stages['stage1']
        self.assertEqual(sorted(list(stage_1.keys())), ['a', 'bar', 'foo'])
        stage_2 = stages['stage2']
        self.assertEqual(sorted(list(stage_2.keys())), ['__interfaces__'])

    @unittest.skipIf(
        sys.version_info[0] >= 3,
        '__metaclass__ property only works in python 2')
    def test_bc_plumbing_py2(self):
        class Behavior1(Behavior):
            a = default(True)

        class BCPlumbing(object):
            __metaclass__ = plumber
            __plumbing__ = Behavior1

        plb = BCPlumbing()
        self.assertTrue(plb.a)


class TestPlumberStage1(unittest.TestCase):

    def test_finalize_instruction(self):
        class Behavior1(Behavior):
            N = finalize('Behavior1')

        class Behavior2(Behavior):
            M = finalize('Behavior2')

        class Base(object):
            K = 'Base'

        @plumbing(Behavior1, Behavior2)
        class Plumbing(Base):
            L = 'Plumbing'

        res = list()
        for x in ['K', 'L', 'M', 'N']:
            res.append("%s from %s" % (x, getattr(Plumbing, x)))
        self.assertEqual(res, [
            'K from Base',
            'L from Plumbing',
            'M from Behavior2',
            'N from Behavior1',
        ])

    def test_finalize_collisions(self):
        err = None

        class Behavior1(Behavior):
            O = finalize(False)

        try:
            @plumbing(Behavior1)
            class Plumbing(object):
                O = True
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left, 'Plumbing class')
            self.assertEqual(err.right.__parent__.__name__, 'Behavior1')
            self.assertEqual(err.right.__class__.__name__, 'finalize')
            self.assertEqual(err.right.__name__, 'O')
            self.assertFalse(err.right.payload)

        class Behavior2(Behavior):
            P = finalize(False)

        try:
            @plumbing(Behavior2)
            class Plumbing(object):
                P = True
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left, 'Plumbing class')
            self.assertEqual(err.right.__parent__.__name__, 'Behavior2')
            self.assertEqual(err.right.__class__.__name__, 'finalize')
            self.assertEqual(err.right.__name__, 'P')
            self.assertFalse(err.right.payload)

        class Behavior3(Behavior):
            Q = finalize(False)

        class Behavior4(Behavior):
            Q = finalize(True)

        try:
            @plumbing(Behavior3, Behavior4)
            class Plumbing(object):
                pass
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__parent__.__name__, 'Behavior3')
            self.assertEqual(err.left.__class__.__name__, 'finalize')
            self.assertEqual(err.left.__name__, 'Q')
            self.assertFalse(err.left.payload)
            self.assertEqual(err.right.__parent__.__name__, 'Behavior4')
            self.assertEqual(err.right.__class__.__name__, 'finalize')
            self.assertEqual(err.right.__name__, 'Q')
            self.assertTrue(err.right.payload)

    def test_override_instruction(self):
        class Behavior1(Behavior):
            K = override('Behavior1')
            M = override('Behavior1')

        class Behavior2(Behavior):
            K = override('Behavior2')
            L = override('Behavior2')
            M = override('Behavior2')

        class Base(object):
            K = 'Base'
            L = 'Base'
            M = 'Base'

        @plumbing(Behavior1, Behavior2)
        class Plumbing(Base):
            K = 'Plumbing'

        res = list()
        for x in ['K', 'L', 'M']:
            res.append("%s from %s" % (x, getattr(Plumbing, x)))
        self.assertEqual(res, [
            'K from Plumbing',
            'L from Behavior2',
            'M from Behavior1'
        ])

    def test_default_instruction(self):
        class Behavior1(Behavior):
            N = default('Behavior1')

        class Behavior2(Behavior):
            K = default('Behavior2')
            L = default('Behavior2')
            M = default('Behavior2')
            N = default('Behavior2')

        class Base(object):
            K = 'Base'
            L = 'Base'

        @plumbing(Behavior1, Behavior2)
        class Plumbing(Base):
            L = 'Plumbing'

        res = list()
        for x in ['K', 'L', 'M', 'N']:
            res.append("%s from %s" % (x, getattr(Plumbing, x)))
        self.assertEqual(res, [
            'K from Base',
            'L from Plumbing',
            'M from Behavior2',
            'N from Behavior1'
        ])

    def test_finalize_wins_over_override(self):
        class Behavior1(Behavior):
            K = override('Behavior1')
            L = finalize('Behavior1')

        class Behavior2(Behavior):
            K = finalize('Behavior2')
            L = override('Behavior2')

        class Base(object):
            K = 'Base'
            L = 'Base'

        @plumbing(Behavior1, Behavior2)
        class Plumbing(Base):
            pass

        res = list()
        for x in ['K', 'L']:
            res.append("%s from %s" % (x, getattr(Plumbing, x)))
        self.assertEqual(res, [
            'K from Behavior2',
            'L from Behavior1'
        ])

    def test_finalize_wins_over_default(self):
        class Behavior1(Behavior):
            K = default('Behavior1')
            L = finalize('Behavior1')

        class Behavior2(Behavior):
            K = finalize('Behavior2')
            L = default('Behavior2')

        class Base(object):
            K = 'Base'
            L = 'Base'

        @plumbing(Behavior1, Behavior2)
        class Plumbing(Base):
            pass

        res = list()
        for x in ['K', 'L']:
            res.append("%s from %s" % (x, getattr(Plumbing, x)))
        self.assertEqual(res, [
            'K from Behavior2',
            'L from Behavior1'
        ])

    def test_override_wins_over_default(self):
        class Behavior1(Behavior):
            K = default('Behavior1')
            L = override('Behavior1')

        class Behavior2(Behavior):
            K = override('Behavior2')
            L = default('Behavior2')

        class Base(object):
            K = 'Base'
            L = 'Base'

        @plumbing(Behavior1, Behavior2)
        class Plumbing(Base):
            pass

        res = list()
        for x in ['K', 'L']:
            res.append("%s from %s" % (x, getattr(Plumbing, x)))
        self.assertEqual(res, [
            'K from Behavior2',
            'L from Behavior1'
        ])

    def test_subclassing_behaviors(self):
        class Behavior1(Behavior):
            J = default('Behavior1')
            K = default('Behavior1')
            M = override('Behavior1')

        class Behavior2(Behavior1):
            # overrides ``J`` of ``Behavior1``
            J = default('Behavior2')
            L = default('Behavior2')
            # this one wins, even if ``M`` on superclass is ``override``
            # instruction due to ordinary inheritance behavior.
            M = default('Behavior2')

        @plumbing(Behavior2)
        class Plumbing(object):
            pass

        plb = Plumbing()
        self.assertEqual(plb.J, 'Behavior2')
        self.assertEqual(plb.K, 'Behavior1')
        self.assertEqual(plb.L, 'Behavior2')
        self.assertEqual(plb.M, 'Behavior2')


class TestPlumberStage2(unittest.TestCase):

    def test_method_pipelines(self):
        res = list()

        class Behavior1(Behavior):
            @plumb
            def __getitem__(_next, self, key):
                res.append("Behavior1 start")
                key = key.lower()
                ret = _next(self, key)
                res.append("Behavior1 stop")
                return ret

        class Behavior2(Behavior):
            @plumb
            def __getitem__(_next, self, key):
                res.append("Behavior2 start")
                ret = 2 * _next(self, key)
                res.append("Behavior2 stop")
                return ret

        Base = dict

        @plumbing(Behavior1, Behavior2)
        class Plumbing(Base):
            pass

        plb = Plumbing()
        plb['abc'] = 6
        self.assertEqual(plb['AbC'], 12)
        self.assertEqual(res, [
            'Behavior1 start',
            'Behavior2 start',
            'Behavior2 stop',
            'Behavior1 stop'
        ])

    def test_endpoint_not_exists(self):
        err = None

        class Behavior1(Behavior):
            @plumb
            def foo(_next, self):
                pass                                         # pragma: no cover

        try:
            @plumbing(Behavior1)
            class Plumbing(object):
                pass
        except AttributeError as e:
            err = e
        finally:
            self.assertEqual(
                str(err),
                'type object \'Plumbing\' has no attribute \'foo\''
            )

    def test_plumb_if_exists(self):
        class Behavior1(Behavior):
            @plumbifexists
            def foo(_next, self):
                pass                                         # pragma: no cover

            @plumbifexists
            def bar(_next, self):
                return 2 * _next(self)

        @plumbing(Behavior1)
        class Plumbing(object):

            def bar(self):
                return 6

        self.assertFalse(hasattr(Plumbing, 'foo'))
        self.assertEqual(Plumbing().bar(), 12)

    def test_property_pipelines(self):
        class Behavior1(Behavior):
            @plumb
            @property
            def foo(_next, self):
                return 2 * _next(self)

        @plumbing(Behavior1)
        class Plumbing1(object):

            @property
            def foo(self):
                return 3

        plb = Plumbing1()
        self.assertEqual(plb.foo, 6)

        class Behavior2(Behavior):
            @plumb
            @property
            def foo(_next, self):
                return 2 * _next(self)

        class Behavior3(Behavior):
            def set_foo(self, value):
                self._foo = value
            foo = plumb(property(
                None,
                override(set_foo),
                ))

        @plumbing(Behavior2, Behavior3)
        class Plumbing2(object):

            @property
            def foo(self):
                return self._foo

        plb = Plumbing2()
        plb.foo = 4
        self.assertEqual(plb.foo, 8)

    def test_subclassing_behaviors(self):
        class Behavior1(Behavior):

            @plumb
            def foo(_next, self):
                return 'Behavior1 ' + _next(self)

            @plumb
            def bar(_next, self):
                return 'Behavior1 ' + _next(self)

        class Behavior2(Behavior1):

            @plumb
            def foo(_next, self):
                return 'Behavior2 ' + _next(self)

        @plumbing(Behavior2)
        class Plumbing(object):

            def foo(self):
                return 'foo'

            def bar(self):
                return 'bar'

        plb = Plumbing()
        self.assertEqual(plb.foo(), 'Behavior2 Behavior1 foo')
        self.assertEqual(plb.bar(), 'Behavior1 bar')

    def test_mixing_properties_and_methods(self):
        err = None

        class Behavior1(Behavior):
            @plumb
            def foo(_next, self):
                return _next(self)                           # pragma: no cover

        try:
            @plumbing(Behavior1)
            class Plumbing(object):

                @property
                def foo(self):
                    return 5                                 # pragma: no cover
        except PlumbingCollision as e:
            err = e
        finally:
            self.assertEqual(err.left.__parent__.__name__, 'Behavior1')
            self.assertEqual(err.left.__class__.__name__, 'plumb')
            self.assertEqual(err.left.__name__, 'foo')
            self.assertEqual(err.left.payload.__name__, 'foo')
            self.assertEqual(err.right.__name__, 'Plumbing')
            self.assertTrue(inspect.isclass(err.right))

    def test_docstrings_joined(self):
        class P1(Behavior):
            """P1
            """
            @plumb
            def foo(self):
                """P1.foo
                """
            bar = plumb(property(None, None, None, "P1.bar"))

        class P2(Behavior):
            @override
            def foo(self):
                """P2.foo
                """
            bar = plumb(property(None, None, None, "P2.bar"))

        @plumbing(P1, P2)
        class Plumbing(object):
            """Plumbing
            """
            bar = property(None, None, None, "Plumbing.bar")

        self.assertEqual(Plumbing.__doc__.strip(), 'Plumbing\n\nP1')
        self.assertEqual(Plumbing.foo.__doc__.strip(), 'P2.foo\n\nP1.foo')
        self.assertEqual(
            Plumbing.bar.__doc__.strip(),
            'Plumbing.bar\n\nP2.bar\n\nP1.bar'
        )

    def test_slots(self):
        class P1(Behavior):
            @default
            def somewhing_which_writes_to_foo(self, foo_val):
                self.foo = foo_val

        @plumbing(P1)
        class WithSlots(object):
            __slots__ = 'foo'

        self.assertEqual(
            type(WithSlots.__dict__['foo']).__name__,
            'member_descriptor'
        )
        ob = WithSlots()
        ob.somewhing_which_writes_to_foo('foo')
        self.assertEqual(ob.foo, 'foo')

    def test_zope_interface(self):
        class IBase(Interface):
            pass

        @implementer(IBase)
        class Base(object):
            pass

        self.assertTrue(IBase.implementedBy(Base))

        class IBehavior1(Interface):
            pass

        @implementer(IBehavior1)
        class Behavior1(Behavior):
            blub = 1

        class IBehavior2Base(Interface):
            pass

        @implementer(IBehavior2Base)
        class Behavior2Base(Behavior):
            pass

        class IBehavior2(Interface):
            pass

        @implementer(IBehavior2)
        class Behavior2(Behavior2Base):
            pass

        self.assertTrue(IBehavior1.implementedBy(Behavior1))
        self.assertTrue(IBehavior2Base.implementedBy(Behavior2Base))
        self.assertTrue(IBehavior2Base.implementedBy(Behavior2))
        self.assertTrue(IBehavior2.implementedBy(Behavior2))

        class IPlumbingClass(Interface):
            pass

        @implementer(IPlumbingClass)
        @plumbing(Behavior1, Behavior2)
        class PlumbingClass(Base):
            pass

        self.assertTrue(IPlumbingClass.implementedBy(PlumbingClass))
        self.assertTrue(IBase.implementedBy(PlumbingClass))
        self.assertTrue(IBehavior1.implementedBy(PlumbingClass))
        self.assertTrue(IBehavior2.implementedBy(PlumbingClass))
        self.assertTrue(IBehavior2Base.implementedBy(PlumbingClass))

        plb = PlumbingClass()

        self.assertTrue(IPlumbingClass.providedBy(plb))
        self.assertTrue(IBase.providedBy(plb))
        self.assertTrue(IBehavior1.providedBy(plb))
        self.assertTrue(IBehavior2.providedBy(plb))
        self.assertTrue(IBehavior2Base.providedBy(plb))


if __name__ == '__main__':
    unittest.main()                                          # pragma: no cover
