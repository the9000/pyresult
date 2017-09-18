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

    def bind(self, func, *args, **kwargs):
        if args or kwargs:
            func = functools.partial(func, *args, **kwargs)
        return func(self.value)

    def and_then(self, func, *args, **kwargs):
        return self.__class__(self.bind(func, *args, **kwargs))

    def __repr__(self):
        return u'%s(%r)' % (self.__class__.__name__, self.value)

    __len__.__doc__ = __len__.__doc__ % cls.__name__

    cls.error = property(error)
    cls.__eq__ = __eq__
    cls.__len__ = __len__
    cls.bind = cls.__rshift__ = bind
    cls.and_then =  cls.__and__ = and_then
    cls.__repr__ = __repr__
    return cls


def _make_left(cls):
    # A decorator that adde "what's-left-oriented" methods to a class.
    def __len__(self):  # Use for len()
        return 0

    len_doc =  """Returns 0, for %s is always falsy.""" % cls.__name__
    __len__.__doc__ = len_doc

    def return_self(self, func, *args, **kwargs):
        """Ignore any attempts to process further."""
        return self

    cls.__len__ = __len__
    cls.and_then =  cls.__and__ = cls.bind = cls.__rshift__ = return_self
    # NOTE: no or_else.
    return cls


def _is_not_none(value):
    """The default .of() predicate."""
    return value is not None
