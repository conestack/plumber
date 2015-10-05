# Python compatibility support code
# This is taken from six


def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        slots = orig_vars.get('__slots__')
        # since add_metaclass is only used for behaviormetaclass, slots related
        # code gets never called. we keep this snippet from the original
        # code anyway and mark coverage report to ignore it.
        if slots is not None:
            if isinstance(slots, str):                       #pragma NO COVER
                slots = [slots]                              #pragma NO COVER
            for slots_var in slots:                          #pragma NO COVER
                orig_vars.pop(slots_var)                     #pragma NO COVER
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper
