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
        raise ValueError('No .error in %r' % self)
    
    def __len__(self):  # Use for len()
        """Returns 1, for %s is always truthy."""
        return 1

    def and_then(self, func, *args, **kwargs):
        if args or kwargs:
            func = functools.partial(func, *args, **kwargs)
        return self.__class__(func(self.value))

    def or_else(self, func, *args, **kwargs):
        return self  # 'else' cannot happen since we're Right.

    def __repr__(self):
        return u'%s(%r)' % (self.__class__.__name__, self.value)

    __len__.__doc__ = __len__.__doc__ % cls.__name__

    cls.error = property(error)
    cls.__len__ = __len__
    cls.and_then =  cls.__and__ = and_then 
    cls.or_else =  cls.__or__ = or_else
    cls.__repr__ = __repr__
    return cls


def _make_left(cls):
    # A decorator that adde "what's-left-oriented" methods to a class.
    def __len__(self):  # Use for len()
        return 0

    len_doc =  """Returns 0, for %s is always falsy.""" % cls.__name__
    __len__.__doc__ = len_doc
    
    def and_then(self, func, *args, **kwargs):
        """Ignore any attempts to process further."""
        return self

    cls.__len__ = __len__ 
    cls.and_then =  cls.__and__ = and_then
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
    def of(cls, value):
        """If value is None, then Some, else Nothing."""
        return cls.Nothing if value is None else cls.Some(value)

    @classmethod
    def of_true(cls, value):
        """If value is truthy, then Some, else Nothing."""
        return cls.Nothing if not value else cls.Some(value)

    @classmethod
    def first(cls, seq):
        """Utility: get the first element of the sequence if it exists, else Nothing"""
        for x in seq:
            return cls.Some(x)
        return cls.Nothing

    
def lift(func, *args, **kwargs):
    def lifted(wrapped_value):
        return wrapped_value.and_then(func, *args, **kwargs)
    lifted.__name__ += ('-' + func.__name__)
    return lifted


Some = Option.Some
Nothing = Option.Nothing


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

        __rshift__ = and_then  # reminiscent of ">>="

        # TODO: unify implentation with _Right.and_then.
        def or_else(self, func, *args, **kwargs):
            """Wrong(a)  -> Wrong(func(a))"""
            if args or kwargs:
                func = functools.partial(func, *args, **kwargs)
            return self.__class__(func(self.__payload))

        __or__ = or_else

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


Right = Either.Right
Wrong = Either.Wrong


def collect_values(seq):
    """Returns a list of values for each Right or Some element in seq."""
    return [x.value for x in seq if x]


def collect_errors(seq):
    """Returns a list of errors for each Wrong element in seq."""
    return [x.error for x in seq if not x]


__all__ = ['Either', 'Right', 'Wrong', 'Option', 'Some', 'Nothing']
