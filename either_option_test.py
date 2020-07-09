"""
Tests for either_option.

Intended to be run with py.test, thus bare asserts.
"""

import itertools

import pytest

import either_option as EO


FALSY_OBJECTS = (False, 0, '', [], {}, set(), EO.Nothing)  # but not None.
TRUTHY_OBJECTS = ([1], 98978876, set(['a', 'Z']), {'foo': 'bar'})


class TestOptionNothing(object):

    def test_nothing_is_falsy(self):
        assert not EO.Nothing

    def test_nothing_has_no_value(self):
        assert not EO.Nothing.has_value

    def test_nothing_cannot_give_value(self):
        with pytest.raises(AttributeError):
            EO.Nothing.value

    def test_nothing_is_not_callable(self):
        assert not callable(EO.Nothing)

    def test_nothing_value_or_returns_alternative(self):
        unique_thing = object()
        assert EO.Nothing.value_or(unique_thing) == unique_thing

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

    def test_nothing_repr_is_nothing(self):
        assert repr(EO.Nothing) == 'Nothing'


class TestOptionSome(object):

    def test_some_is_truthy(self):
        objects = FALSY_OBJECTS + TRUTHY_OBJECTS
        results = [(x, EO.Some(x)) for x in objects]
        wrong = filter(lambda (x, result): not result, results)
        assert not wrong

    def test_some_has_value(self):
        assert EO.Some(1).has_value

    def test_some_value_or_returns_value(self):
        assert EO.Some(111).value_or(222) == 111

    def rest_option_of_is_some_for_falsy_data(self):
        resuts = [(x, EO.of(x)) for x in FALSY_OBJECTS]
        wrong = filter(lambda (x, result): result is EO.Nothing, results)
        assert not wrong

    def test_option_of_wraps_the_original_objects(self):
        objects = FALSY_OBJECTS + TRUTHY_OBJECTS
        results = [(x, EO.Option.of(x)) for x in objects]
        wrong = filter(lambda (x, result): result.value is not x, results)
        assert not wrong

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
        assert EO.Some('1f').and_then(int, 16) == EO.Some(31)

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

    def test_bind_accepts_method_name(self):
        assert EO.Some('foo').bind('upper') == 'FOO'

    def test_bind_accepts_method_name_and_args(self):
        assert EO.Some('(foo)').bind('strip', '()') == 'foo'

    def test_bind_is_infix_rshift(self):
        assert EO.Some('   joe   ') >> str.strip == 'joe'

    def test_rbind_accepts_arguments(self):
        assert EO.Some(['a', 'b', 'c']).rbind(str.join, '-') == 'a-b-c'

    def test_rbind_passes_self_last(self):
        assert EO.Some([1, 2]).rbind(map, str) == ['1', '2']


class FailingSeq(object):
    # Fails at any any attempt of iterating over it.
    def __iter__(self):
        assert False, 'Attempt to iterate'

    next = __iter__


class TestOptionClass(object):

    def test_first_of_non_empty_sequence_is_some(self):
        assert EO.Option.first([1, 2, 3]) == EO.Some(1)

    def test_first_of_empty_sequence_is_nothing(self):
        assert EO.Option.first([]) == EO.Nothing

    def test_first_is_lazy(self):
        only_once_seq = itertools.chain([1], FailingSeq())
        assert EO.Option.first(only_once_seq) == EO.Some(1)

    def test_sequence_of_some_is_some(self):
        assert (EO.Option.sequence([EO.Some(1), EO.Some("foo")]) ==
                EO.Some([1, "foo"]))

    def test_sequence_of_some_is_list(self):
        assert (EO.Option.sequence((EO.Some(1), EO.Some("foo")))
                == EO.Some([1, "foo"]))

    def test_sequence_with_nothing_is_nothing(self):
        assert (EO.Option.sequence((EO.Some(1),EO.Nothing, EO.Some("foo")))
                is EO.Nothing)

    def test_sequence_with_nothing_short_circuits(self):
        def boom_seq():
            yield EO.Some(1)
            yield EO.Nothing
            raise Exception("boom!")
            yield EO.Some(2)

        assert EO.Option.sequence(boom_seq()) is EO.Nothing

    def test_empty_sequence_is_some(self):
        assert EO.Option.sequence(()) == EO.Some([])

    def test_pack_removes_nothing(cls):
        assert (EO.Option.pack((EO.Some(1),EO.Nothing, EO.Some("foo")))
                == EO.Some([1, "foo"]))

    def test_pack_works_without_nothing(cls):
        assert (EO.Option.pack((EO.Some(1),EO.Some(None), EO.Some("foo")))
                == EO.Some([1, None, "foo"]))

    def test_pack_works_on_empty_sequence(cls):
        assert (EO.Option.pack([]) == EO.Some([]))


class TestIteration(object):

    def test_nothing_does_empty_loop(self):
        assert list(EO.Nothing) == []

    def test_either_does_empty_loop_by_wrong(self):
        assert list(EO.Wrong("joe")) == []

    def test_some_does_one_loop(self):
        assert list(EO.Some('thing')) == ['thing']

    def test_either_does_loop_by_right(self):
        assert list(EO.Right("joe")) == ["joe"]


class TestEitherRight(object):

    def test_right_has_value(self):
        arbitrary = object()
        assert EO.Right(arbitrary).value == arbitrary

    def test_right_has_no_error(self):
        with pytest.raises(AttributeError):
            EO.Right(1).error

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

    def test_inverse_is_wrong(self):
        arbitrary = object()
        # TODO: rename to .inverted().
        assert EO.Right(arbitrary).inverse() == EO.Wrong(arbitrary)


# Utility for interactive debugging.
"""
def reload_EO():
    import sys
    targets = [module for (name, module) in sys.modules.items()
               if module and 'either_option' in name]
    for target in sorted(targets):
        old_id = id(target)
        new_id = id(reload(target))
        print 'Reloaded %r: %x -> %x' % (target, old_id, new_id)
"""
def unload_EO():
    import sys
    new_modules = {name: module for (name, module) in sys.modules.items()
                   if module and 'either_option' not in name}
    sys.modules = new_modules
