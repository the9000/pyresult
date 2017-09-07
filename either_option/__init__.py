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

from option import *
from either import *

# TODO: Either move to a separate file or eschew.
def lift(func, *args, **kwargs):
    def lifted(wrapped_value):
        return wrapped_value.and_then(func, *args, **kwargs)
    lifted.__name__ += ('-' + func.__name__)
    return lifted
