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
        """Returns 1, for %s is always truthy."""
        return 1

    def rbind(self, func, *args, **kwargs):
        # call callables, assume strings method names.
        if not callable(func):
            func = getattr(self.value.__class__, func)  # Will crash on wrong method name.
        return func(*(args + (self.value,)), **kwargs)

    def bind(self, func, *args, **kwargs):
        # call callables, assume strings method names.
        if not callable(func):
            func = getattr(self.value.__class__, func)  # Will crash on wrong method name.
        return func(*((self.value,) + args), **kwargs)

    def and_then(self, func, *args, **kwargs):
        return self.__class__(self.bind(func, *args, **kwargs))

    def or_value(self, other_value):
        """Returns self.value, ignores other_value."""
        return self.value

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
    cls.or_value = or_value
    cls.error = property(error)
    return cls


def _make_left(cls):
    # A decorator that adde "what's-left-oriented" methods to a class.
    def __len__(self):  # Use for len()
        return 0

    len_doc =  """Returns 0, for %s is always falsy.""" % cls.__name__
    __len__.__doc__ = len_doc

    cls.__len__ = __len__
    cls.and_then =  cls.__and__ = cls.bind = cls.rbind = cls.__rshift__ = _return_self
    # NOTE: no or_else / `|`.

    def or_value(self, other_value):
        """Returns other_value, because self.value does not exist."""
        return other_value

    cls.or_value = or_value

    return cls


def _is_not_none(value):
    """The default .of() predicate."""
    return value is not None


def _return_self(self, func, *args, **kwargs):
    """Ignore any attempts to process further."""
    return self
