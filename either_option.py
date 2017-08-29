"""
The few most useful sum types, without the general monadic machinery.

Right/Wrong always pass a value. Some passes a value, but Nothing does not,
Otherwise Right and Some are mostly the same, and Wrong and Nothing are mostly the same.

Use as a normal wrapper object:

    result = compute_soething(...)
    if result:
       return json.dumps(result.value)
    else:
       log.error("Failure: %r", result.error)

Use it in a chain computation that stops on the first error and remembers it:

    result = Right("Joe") >> find_user >> get_user_email & partial(send_mail(body=welcome_email))
    result | log.error  # Only log an error if result is Wrong.


Common methods for M in (Option, Either):

  .bind((a -> M)) -> M
  >> is an alias for bind (think |> or >>= or general idea of a pipeline)

  .and_then((a -> a)) -> M  # aka .map, but we don't use this name.
  & is an alias for and_then , because "and".

  .or_else((a -> a)) -> M
  | is an alias for or_else, because "or".

Wrap exception-based APIs into Right / Wrong:

    Either.catching(IOError)(requests.get, weather_url) >> udate_forecast   # Lame.
"""


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

# TODO: move to its own module, disband the class.
class Option(object):
    """Holder of Some and Nothing, and helpers."""

    @_make_right
    class Some(object):
        """Represent a 'contentful' variant of Option.

        It's truthy, has .value, .and_then() and .bind() proceed.
        """
        __slots__ = ('__payload',)

        def __init__(self, value):
            self.__payload = value

        @property
        def value(self):
            return self.__payload

    @_make_left
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
            predicate = _is_not_none
        return cls.Some(value) if predicate(value) else cls.Nothing  

    @classmethod  # TODO: factor out;
    # Ergonomics of partial application if trumped by arg order matching .of().
    def map_of(cls, seq, predicate):
        """Lazily map .of() over seq."""
        return (cls.of(x, predicate) for x in seq)
    
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

        
def lift(func, *args, **kwargs):
    def lifted(wrapped_value):
        return wrapped_value.and_then(func, *args, **kwargs)
    lifted.__name__ += ('-' + func.__name__)
    return lifted


Some = Option.Some
Nothing = Option.Nothing


def _is_not_none(value):
    return value is not None  # To avoid writin a lambda in Option.of().

def _is_not_nothing(value):
    return value is not Nothing

# TODO Move to a separate file.

class Either(object):
    """Home of Right and Wrong, and helper methods."""

    @_make_right
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


    @_make_left
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
            """Wrong(a)  -> Wrong(func(a))"""
            if args or kwargs:
                func = functools.partial(func, *args, **kwargs)
            return self.__class__(func(self.__payload))

        __or__ = or_else

        def __eq__(self, other):
            return (self.__class__ is other.__class__ and
                    self.error == other.error)

        def __repr__(self):
            return u'%s(%r)' % (self.__class__.__name__, self.error)

        def inverse(self):
            return Either.Right(self.error)

    @classmethod
    def of(cls, value, default):
        """If value is None, then Some, else Nothing."""
        return cls.Wrong(default) if value is None else cls.Right(value)

    @classmethod
    def of_true(cls, value, default):
        """If value is truthy, then Some, else Nothing."""
        return cls.Wrong(default) if not value else cls.Right(value)

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


__all__ = ['Either', 'Right', 'Wrong', 'Option', 'Some', 'Nothing']
