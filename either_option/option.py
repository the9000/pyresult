"""Implementation of Option class."""

from either_option import _impl


class Option(object):
    """Holder of Some and Nothing, and helpers."""

    @_impl._make_right
    class Some(object):
        """Represent a 'contentful' variant of Option.

        It's truthy, has .value, .and_then() and .bind() proceed.
        """
        __slots__ = ('__payload',)

        def __init__(self, value):
            self.__payload = value

        @property  # Cannot factor it out because __payload access.
        def value(self):
            return self.__payload

    @_impl._make_left
    class Nothing(object):
        """Represent an 'empty' variant of Option.

        It's falsy, han ne .value, .and_then() and .bind()
        return immediately."""
        __slots__ = ()  # Allow no attributes.

        def __repr__(self):
            return self.__class__.__name__


    # Replace the nested class with a single instance,
    # removeing any possibility to create more.
    Nothing = Nothing()

    @classmethod
    # Ergonomics of partial application if trumped by default arg convenience.
    def of(cls, value, predicate=None):
        """If predicate(value), then Some, else Nothing.

        Default predicate is `is not None`. Pass `bool` for truth chacking.
        """
        if predicate is None:
            predicate = _impl._is_not_none
        return cls.Some(value) if predicate(value) else cls.Nothing

    @classmethod
    def first(cls, seq):
        """Utility: get the first element of the sequence if it's non-empty, else Nothing"""
        for x in seq:
            return cls.Some(x)
        return cls.Nothing

    @classmethod
    def sequence(cls, seq):  # NOTE: After Haskell and Scalaz.
        """Returns unpacked values of seq if all are Some, else Nothing.

        If each element of seq = [Some(x),...] is Some, return Some([x,..]).
        If any of the elements of seq are Nothing, return Nothing,

        The evaluation is short-circuited: seq is evaluated until the first Nothing.
        Otherwie seq has to be completely evaluated to return a Some.
        """
        collected = []
        for x in seq:
            if x is cls.Nothing:
                return Nothing
            else:
                collected.append(x.value)
        return Some(collected)

    @classmethod
    def pack(cls, seq):
        """Remove all Nothings from the seq, .sequence the rest."""
        return cls.sequence(filter(_is_not_nothing, seq))


def _is_not_nothing(value):
    return value is not Nothing


Some = Option.Some
Nothing = Option.Nothing


__all__ = ['Option', 'Some', 'Nothing']
