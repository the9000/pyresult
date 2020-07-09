"""Implementation of left and right, common parts of both Option and Either."""

import functools


def _make_right(cls):
    # A decorator that adds "that's-right-oriented" methods to a class.

    def error(self):
        # Help stacktraces a bit.
        raise AttributeError('No .error in %r' % self)

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.value == other.value)

    def __len__(self):  # Use for len()
        """Lifted into %s: returns len() of the value"""
        return len(self.value)

    def rbind(self, func, *args, **kwargs):
        # No method names accepted.
        return func(*(args + (self.value,)), **kwargs)

    def bind(self, func_or_name, *args, **kwargs):
        # call callables, assume strings method names.
        if not callable(func_or_name):
            func = getattr(self.value.__class__, func_or_name)  # Will crash on wrong method name.
        else:
            func = func_or_name
        return func(*((self.value,) + args), **kwargs)

    def and_then(self, func, *args, **kwargs):
        return self.__class__(self.bind(func, *args, **kwargs))

    def value_or(self, other_value):
        """Returns self.value, ignores other_value."""
        return self.value

    def has_value(self):
        return True

    cls.has_value = property(has_value)

    def __repr__(self):
        return u'%s(%r)' % (self.__class__.__name__, self.value)

    __len__.__doc__ = __len__.__doc__ % cls.__name__

    cls.__repr__ = __repr__
    # Lifted utilities.
    cls.__eq__ = __eq__
    cls.__len__ = __len__

    # Positive.
    cls.bind = cls.__rshift__ = bind
    cls.rbind = rbind
    cls.and_then =  cls.__and__ = and_then
    # Negative.
    cls.value_or = value_or
    cls.error = property(error)

    # Iteration / "fmap"
    def __iter__(self):
        return iter((self.value,))

    cls.__iter__ = __iter__

    return cls


def _make_left(cls):
    # A decorator that adde "what's-left-oriented" methods to a class.
    # def __len__(self):  # Use for len()
    #     return 0

    # len_doc =  """Returns 0, for %s is always falsy.""" % cls.__name__
    # __len__.__doc__ = len_doc

    # cls.__len__ = __len__
    # cls.and_then =  cls.__and__ = cls.bind = cls.rbind = cls.__rshift__ = _return_self
    # NOTE: no or_else / `|`.

    def value_or(self, other_value):
        """Returns other_value, because self.value does not exist."""
        return other_value

    cls.value_or = value_or

    def has_value(self):
        return False

    cls.has_value = property(has_value)

    def __iter__(self):
        return _EMPTY_ITER

    cls.__iter__ = __iter__

    return cls


def _is_not_none(value):
    """The default .of() predicate."""
    return value is not None


def _return_self(self, func, *args, **kwargs):
    """Ignore any attempts to process further."""
    return self

_EMPTY_ITER = iter(())  # Always empty, no state, can be reused.


# Lifting of methods.
# TODO: Lifting of value attributes.
# Some("foo").lifted.upper() == Some("FOO")
# Some("foo").lifted[0] == Some("f")
# Nothing.lifted.anything() == Nothing.

class _Lifted(object):
    __slots__ = ("__value")

    def __init__(self, rightish):
        self.__value = rightish

    def __getattr__(self, name):
        attr = getattr(self.__value)
        if callable(attr):
            return lambda *args, **kwargs: self.__value.__class(attr(*args, **kwargs))
