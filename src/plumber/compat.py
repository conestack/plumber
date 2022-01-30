# Python compatibility support code
import sys


IS_PY2 = sys.version_info[0] < 3
ITER_FUNC = 'iteritems' if IS_PY2 else 'items'
STR_TYPE = basestring if IS_PY2 else str


def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    # This is taken from six
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        slots = orig_vars.get('__slots__')
        # since add_metaclass is only used for behaviormetaclass, slots related
        # code gets never called. we keep this snippet from the original
        # code anyway and mark coverage report to ignore it.
        if slots is not None:
            if isinstance(slots, str):  # pragma: no cover
                slots = [slots]
            for slots_var in slots:  # pragma: no cover
                orig_vars.pop(slots_var)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper
