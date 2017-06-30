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

    result = Right("Joe") >> find_user >> get_user_email >> partial(send_mail(body=welcome_email))
    result ^ log.error  # Only log an error if result is Left.


Wrap exception-based APIs into Right / Wrong:

    Either.catching(IOError)(requests.get, weather_url) >> udate_forecast   # Lame.
"""


class _Right(object):
    """Base for 'sucessful' results"""
    __slots__ = ['__payload']
    
    def __init__(self, value):
        self.__payload = value

    @property
    def value(self):
        return self.__payload

    @property
    def error(self):
        # Help stacktraces a bit.
        raise ValueError('No .error in %r' % self)

    def __len__(self):
        """Some(...) is always truthy."""
        return 1

    def and_then(self, func, *args, **kwargs):
        """Some(a) -> func(a)"""
        return func(*(args + (self.value,)), **kwargs)

    __rshift__ = and_then  # reminiscent of ">>="

    def or_else(self, func):
        return self  # 'else' did not happen.

    __xor__ = or_else

    def map(self, func):
        """Some(a)  -> Some(func(a))"""
        return self.__class__(func(self.value))

    __mod__ = map  # % somehow reminiscent of "<$>"

    def __repr__(self):
        return u'%s(%r)' % (self.__class__.__name__, self.value)


class Option(object):
    """Holder of Some and Nothing, and helpers."""

    # TODO: switch to class decorators to keep the slots useful.
    class Some(_Right):
        pass  # The same thing so far.

    class Nothing(object):
        __slots__ = []  # Allow no attributes.
        
        def and_then(self, func):
            """Ignore any attempts to process further."""
            return self

        __rshift__ = and_then  # reminiscent of ">>="

        def map(self, func):
            """Ignore any attempts to process further."""
            return self

        __mod__ = map  

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


Some = Option.Some
Nothing = Option.Nothing


class Either(object):
    """Home of Right and Wrong, and helper methods."""

    class Right(_Right):
        """The Right outcome, with and_then() continuing the chain."""
        def inverse(self):
            return Either.Wrong(self.value)

    class Wrong(object):
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

        def __len__(self):
            """Wrong(...) is always falsy."""
            return 0

        def and_then(self, func):
            return self  # 'else' did not happen.

        __rshift__ = and_then  # reminiscent of ">>="

        def or_else(self, func):
            """Wrong(a) -> func(a)"""
            return func(self.error)

        __xor__ = or_else

        def map(self, func):
            """Some(a)  -> Some(func(a))"""
            return self.__class__(func(self.value))

        __mod__ = map  # % is somehow reminiscent of "<$>"

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
