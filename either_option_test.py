"""
Tests for either_option.

Intended to be run with py.test, thus bare asserts.
"""

import pytest

import either_option as EO


class TestOption(object):

    FALSY_OBJECTS = (False, 0, '', [], {}, set(), EO.Nothing)  # but not None.

    def test_nothing_is_falsy(self):
        assert not EO.Nothing
    
    def test_nothing_is_not_callable(self):
        assert not callable(EO.Nothing)

    def test_option_of_none_is_nothing(self):
        assert EO.Option.of(None) is EO.Nothing
        
    def test_option_of_true_is_nothing_for_false(self):
        assert EO.Option.of_true(False) is EO.Nothing

    def test_option_of_true_is_same_for_various_inputs(self):
        results = [(x, EO.Option.of_true(x))
                   for x in self.FALSY_OBJECTS + (None,)]
        wrong = filter(lambda (x, result): result is not EO.Nothing, results)
        assert not wrong
        
    def test_nothing_is_singleton(self):
        # Weak but still useful for sanity check and stating the intent.
        EO.Option.of(None) is EO.Option.of_true(False)

    def rest_option_of_is_some_for_falsy_data(self):
        resuts = [(x, EO.of(x)) for x in self.FALSY_OBJECTS]
        wrong = filter(lambda (x, result): result is EO.Nothing, results)
        assert not wrong

    def test_option_of_wraps_the_objects(self):
        objects = self.FALSY_OBJECTS + ([1], 98978876, set(['a', 'Z']), {'foo': 'bar'})
        results = [(x, EO.Option.of(x)) for x in objects]
        wrong = filter(lambda (x, result): result.value is not x, results)
        assert not wrong
