from decimal import Decimal

import pytest

from num2words.currency import parse_currency_parts


def test_verify_parse_currency_parts():
    # int is treated as cents by default
    assert parse_currency_parts(1234) == (12, 34, False)
    assert parse_currency_parts(-150) == (1, 50, True)
    assert parse_currency_parts(7) == (0, 7, False)
    # int treated as whole units when is_int_with_cents is False
    assert parse_currency_parts(1234, is_int_with_cents=False) == (1234, 0, False)
    assert parse_currency_parts(-5, is_int_with_cents=False) == (5, 0, True)
    # strings and Decimal are rounded half up to two decimal places
    assert parse_currency_parts('12.345') == (12, 35, False)
    assert parse_currency_parts('-0.005') == (0, 1, True)
    assert parse_currency_parts(Decimal('-0.5')) == (0, 50, True)
    assert parse_currency_parts(Decimal('3')) == (3, 0, False)
    # float is converted through its string form
    assert parse_currency_parts(1.5) == (1, 50, False)
    assert parse_currency_parts(0) == (0, 0, False)


def test_verify_parse_currency_parts_invalid_string():
    from decimal import InvalidOperation

    with pytest.raises(InvalidOperation):
        parse_currency_parts('abc')
