import pytest

from num2words import num2words


def test_verify_cardinal_reading():
    assert num2words(21) == 'twenty-one'
    assert num2words(1234.5, lang='es') == 'mil doscientos treinta y cuatro punto cinco'


def test_verify_ordinal_reading():
    assert num2words(3, ordinal=True) == 'third'
    assert num2words(3, lang='en', to='ordinal_num') == '3rd'


def test_verify_year_reading():
    assert num2words(1984, lang='en', to='year') == 'nineteen eighty-four'


def test_verify_currency_reading():
    assert num2words(12.34, lang='en', to='currency') == 'twelve euro, thirty-four cents'
    assert num2words(2.14, lang='es', to='currency') == 'dos euros con catorce céntimos'


def test_verify_language_selection():
    # a regional code falls back to its language code
    assert num2words(5, lang='en_US') == 'five'
    assert num2words(5, lang='en_GB') == 'five'
    with pytest.raises(NotImplementedError):
        num2words(1, lang='xx')
    with pytest.raises(NotImplementedError):
        num2words(1, lang='en', to='bogus')
