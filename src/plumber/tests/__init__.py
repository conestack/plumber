from __future__ import print_function
from plumber import Behavior
from plumber import default
from plumber import finalize
from plumber import override
from plumber import plumb
from plumber import plumbifexists
from plumber import plumbing
from plumber.exceptions import PlumbingCollision
from pprint import pprint
from zope.interface import Interface
from zope.interface import implementer
import doctest
import inspect

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestInstructions(unittest.TestCase):

    def assertRaisesWithMessage(self, msg, func, exc, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except exc as inst:
            self.assertEqual(str(inst), msg)


class TestBehaviors(unittest.TestCase):
    pass


class TestPlumber(unittest.TestCase):
    pass


class TestGlobalMetaclass(unittest.TestCase):
    pass


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
                pass

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
                pass

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
                return _next(self)

        try:
            @plumbing(Behavior1)
            class Plumbing(object):

                @property
                def foo(self):
                    return 5
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


###############################################################################
# OLD stuff
###############################################################################

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE


TESTFILES = [
    '../plumber.rst',
]
TESTMODULES = [
    'plumber._instructions',
    'plumber._behavior',
    'plumber._plumber',
    'plumber.tests._globalmetaclasstest',
]


def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite(
            module,
            optionflags=optionflags,
            ) for module in TESTMODULES
        ]+[
        doctest.DocFileSuite(
            file,
            optionflags=optionflags,
            globs={#'interact': interact,
                   'pprint': pprint,
                   'print': print},
            ) for file in TESTFILES
        ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')                 #pragma NO COVER
