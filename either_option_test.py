"""
Tests for either_option.

Intended to be run with py.test, thus bare asserts.
"""

import pytest

import either_option as EO


FALSY_OBJECTS = (False, 0, '', [], {}, set(), EO.Nothing)  # but not None.
TRUTHY_OBJECTS = ([1], 98978876, set(['a', 'Z']), {'foo': 'bar'})


class TestOptionNothing(object):

    def test_nothing_is_falsy(self):
        assert not EO.Nothing

    def nothing_has_no_value(self):
        with pythest.assert_raises(AttributeError):
            EO.Nothing.value

    def test_nothing_is_not_callable(self):
        assert not callable(EO.Nothing)

    def test_option_of_none_is_nothing(self):
        assert EO.Option.of(None) is EO.Nothing

    def test_option_of_predicate_is_nothing_for_false_predicate(self):
        assert EO.Option.of('1', str.isalpha) is EO.Nothing

    def test_nothing_is_singleton(self):
        # Weak but still useful for sanity check and stating the intent.
        EO.Option.of(None) is EO.Option.of(False, bool)

    def test_bind_ignores_arguments_returns_self(self):
        assert EO.Nothing.bind(str, foo='bar') is EO.Nothing

    def test_and_then_ignores_arguments_returns_self(self):
        assert EO.Nothing.and_then(str, foo='bar') is EO.Nothing

    def test_and_bind_return_self(self):
        def boom(x):
            raise Exception(x)
        assert (EO.Nothing & boom) is EO.Nothing
        assert (EO.Nothing >> boom) is EO.Nothing


class TestOptionSome(object):

    def test_some_is_truthy(self):
        objects = FALSY_OBJECTS + TRUTHY_OBJECTS
        results = [(x, EO.Some(x)) for x in objects]
        wrong = filter(lambda (x, result): not result, results)
        assert not wrong

    def rest_option_of_is_some_for_falsy_data(self):
        resuts = [(x, EO.of(x)) for x in FALSY_OBJECTS]
        wrong = filter(lambda (x, result): result is EO.Nothing, results)
        assert not wrong

    def test_option_of_wraps_the_original_objects(self):
        objects = FALSY_OBJECTS + TRUTHY_OBJECTS
        results = [(x, EO.Option.of(x)) for x in objects]
        wrong = filter(lambda (x, result): result.value is not x, results)
        assert not wrong

    def nothing_has_no_value(self):
        with pythest.assert_raises(AttributeError):
            EO.Some(1).error

    def test_some_instances_equal_when_values_equal(self):
        one = {'foo': 'moo'}
        other = one.copy()
        assert EO.Some(one) == EO.Some(other)

    def test_some_instances_unequal_when_values_unequal(self):
        one = {'foo': 'moo'}
        other = {'moo': 'bar'}
        assert EO.Some(one) != EO.Some(other)

    def test_and_then_wraps_transformed_value(self):
        assert EO.Some(123).and_then(str) == EO.Some('123')

    def test_and_then_equals_to_and(self):
        assert EO.Some([123]).and_then(str) == EO.Some([123]) & str

    def test_and_then_passes_args(self):
        assert EO.Some([1, 2]).and_then(map, str) == EO.Some(['1', '2'])

    def test_and_then_passes_kwargs(self):
        assert (EO.Some(u'\xe9').and_then(unicode.encode, encoding='utf-8') ==
                EO.Some('\xc3\xa9'))

    def test_bind_does_not_wrap(self):
        # In a statically checked language, a type system would check that.
        assert EO.Some(1).bind(str) == '1'

    def test_bind_accepts_arguments(self):
        def foo(x, value, transf):
            return EO.Some(transf(x + value))
        assert EO.Some(1).bind(foo, 2, transf=str) == EO.Some('3')


class TestEitherRight(object):

    def test_or_else_returns_self(self):
        s = EO.Right(1)
        assert s.or_else(str) is s

    def test_or_else_ignores_function(self):
        s = EO.Right(1)
        def boom(x):
            raise Exception(x)
        assert s.or_else(boom) is s

    def test_or_else_ignores_function_params(self):
        s = EO.Right(1)
        assert s.or_else(str, 1, foo='bar') is s

    def test_or_else_equals_or(self):
        s = EO.Right(1)
        assert s.or_else(str) is (s | str)
