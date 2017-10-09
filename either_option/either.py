# Implementation of Either.

from either_option import _impl


class Either(object):
    """Home of Right and Wrong, and helper methods."""

    @_impl._make_right
    class Right(object):
        """The "that's right" variant of Option.

        It's truthy, has .value, .and_then() and .bind() proceed.
        """
        __slots__ = ('__payload',)

        def __init__(self, value):
            self.__payload = value

        @property
        def value(self):
            return self.__payload

        def or_else(self, func, *args, **kwargs):
            return self  # 'else' cannot happen since we're Right.

        __or__ = or_else

        def inverse(self):
            return Either.Wrong(self.value)


    @_impl._make_left
    class Wrong(object):
        """The "what's wrong" variant of Either.

        It's falsy, has .error but no .value, .and_then() and .bind() short-circuit
        to return this same Wrong; .or_else proceeds.
        """
        __slots__ = ['__payload']

        def __init__(self, value):
            self.__payload = value

        @property
        def value(self):
            # Help stacktraces a bit.
            raise ValueError('No .value in %r' % self)

        @property
        def error(self):
            return self.__payload

        def and_then(self, func, *args, **kwargs):
            return self  # 'else' did not happen.

        __and__ = bind = __rshift__ = and_then

        # TODO: unify implentation with Some.and_then.
        def or_else(self, func, *args, **kwargs):
            """Wrong(a)  -> Right(func(a))"""
            return self.inverse().and_then(func, *args, **kwargs)

        __or__ = or_else

        def __eq__(self, other):
            return (self.__class__ is other.__class__ and
                    self.error == other.error)

        def __repr__(self):
            return u'%s(%r)' % (self.__class__.__name__, self.error)

        def inverse(self):
            return Either.Right(self.error)

    @classmethod
    def of(cls, value, otherwise, predicate=None):
        """If predicate(value), then Right(value), else Wrong(otherwise).

        Default predicate is `is not None`. Pass `bool` for truth chacking.
        """
        if predicate is None:
            predicate = _impl._is_not_none
        return cls.Right(value) if predicate(value) else cls.Wrong(otherwise)

    @classmethod
    def wrapping(cls, exceptions, func):
        def either_wrapped(*args, **kwargs):
            try:
                return cls.Right(func(*args, **kwargs))
            except exceptions as ex:
                return cls.Wrong(ex)
        return either_wrapped
    
    @classmethod
    def collect(cls, seq):
        """Returns a seq of Right values unpacked, or Wrong value unpacked.

        If each element of seq = [Right(x),...] is Right, return Right([x,..]).
        If some of the elements of [...Wrong(y),..] are Wrong, return
        Wrong([y,...]) for all Wrong elements only.

        >>> Either.collect([Right('hand'), Right('foot)]) == Right(['hand', 'foot'])
        >>> Either.collect([Right('hand'), Wrong('move')]) == Wrong(['move'])
        """
        errors = [x.error for x in seq if not x]
        if errors:
            return Wrong(errors)
        return Right([x.value for x in seq])

    
Right = Either.Right
Wrong = Either.Wrong

__all__ = ["Either", "Right", "Wrong"]
