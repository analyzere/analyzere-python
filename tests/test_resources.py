import pytest

from analyzere import MonetaryUnit


class TestMonetaryUnit:
    def test_init_with_pos_arg(self):
        m = MonetaryUnit(123, 'USD')
        assert m.value == 123
        assert m.currency == 'USD'

        with pytest.raises(TypeError):
            MonetaryUnit(123)

    def test_init_with_kwargs(self):
        m = MonetaryUnit(123, currency='USD')
        assert m.value == 123
        assert m.currency == 'USD'

        m = MonetaryUnit(value=123, currency='USD')
        assert m.value == 123
