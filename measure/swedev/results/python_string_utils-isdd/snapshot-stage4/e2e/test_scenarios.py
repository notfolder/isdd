"""
E2E scenarios for string_utils (one test function per scenario of the detailed design, section 8-2).
The functions are called through the public package interface, as a library user would call them.
"""
import ast
import os
import re
import sys
import uuid as uuid_module

import string_utils
from string_utils import (
    asciify, booleanize, camel_case_to_snake, compress, contains_html, decompress,
    is_camel_case, is_credit_card, is_decimal, is_email, is_full_string, is_integer, is_ip, is_ip_v4,
    is_ip_v6, is_isbn, is_isbn_10, is_isbn_13, is_isogram, is_json, is_number, is_palindrome,
    is_pangram, is_slug, is_snake_case, is_string, is_url, is_uuid, prettify, random_string,
    reverse, roman_decode, roman_encode, roman_range, secure_random_hex, shuffle, slugify,
    snake_case_to_camel, strip_html, strip_margin, uuid, words_count,
)
from string_utils.errors import InvalidInputError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_public_api_import():
    # every name listed in the public __all__ of the modules is available from the package
    for module in (string_utils.validation, string_utils.manipulation, string_utils.generation):
        for name in module.__all__:
            assert callable(getattr(string_utils, name)), name

    # judgement functions return False for non-string input
    assert is_email(None) is False
    assert is_full_string(b'abc') is False
    assert is_credit_card(None) is False

    # transforming functions raise InvalidInputError for non-string input
    with_raises = [lambda: reverse(None), lambda: prettify(None), lambda: slugify(123)]
    for call in with_raises:
        try:
            call()
        except InvalidInputError:
            pass
        else:
            raise AssertionError('InvalidInputError was not raised')

    # the number judgement raises InvalidInputError for non-string input
    try:
        is_number(None)
    except InvalidInputError:
        pass
    else:
        raise AssertionError('InvalidInputError was not raised')


def test_validation_basics():
    assert is_string('a') is True
    assert is_string(b'a') is False
    assert is_full_string(' ') is False
    assert is_full_string('x') is True

    assert is_number('-1.5e3') is True
    assert is_number('1 2 3') is False
    assert is_integer('42') is True
    assert is_integer('4.2') is False
    assert is_decimal('4.2') is True
    assert is_decimal('42') is False

    assert is_url('https://example.com/path?x=1') is True
    assert is_url('not a url') is False
    assert is_url('ftp://example.org', allowed_schemes=['http', 'https']) is False

    assert is_email('john.doe@example.com') is True
    assert is_email('john..doe@example.com') is False

    assert is_json('{"a": 1}') is True
    assert is_json('[1, 2]') is True
    assert is_json('abc') is False

    assert is_uuid('6f8aa2f9-686c-4ac3-8766-5712354a04cf') is True
    assert is_uuid('6f8aa2f9686c4ac387665712354a04cf') is False
    assert is_uuid('6f8aa2f9686c4ac387665712354a04cf', allow_hex=True) is True

    assert is_ip_v4('255.200.100.75') is True
    assert is_ip_v4('255.200.100.999') is False
    assert is_ip_v6('2001:db8:85a3:0000:0000:8a2e:370:7334') is True
    assert is_ip('nope') is False


def test_validation_text():
    assert is_camel_case('camelCase') is True
    assert is_camel_case('snake_case') is False
    assert is_snake_case('snake_case') is True
    assert is_snake_case('camelCase') is False

    assert is_isbn_13('9780306406157') is True
    assert is_isbn_13('9780306406158') is False
    assert is_isbn_10('0306406152') is True
    assert is_isbn('0-306-40615-2') is True

    assert is_palindrome('otto') is True
    assert is_palindrome('i topi non avevano nipoti', ignore_spaces=True) is True
    assert is_palindrome('Otto', ignore_case=True) is True
    assert is_palindrome('Otto') is False

    assert is_pangram('The quick brown fox jumps over the lazy dog') is True
    assert is_pangram('hello world') is False

    assert is_isogram('uncopyrightable') is True
    assert is_isogram('hello') is False

    assert is_slug('my-blog-post') is True
    assert is_slug('My Blog') is False

    assert contains_html('<b>x</b>') is True
    assert contains_html('plain text') is False

    assert words_count('one,two,three.stop') == 4
    assert words_count('! @ # % ... []') == 0


def test_text_transform():
    assert camel_case_to_snake('ThisIsACamelCaseStringTest') == 'this_is_a_camel_case_string_test'
    assert snake_case_to_camel('the_snake_is_green') == 'TheSnakeIsGreen'
    assert snake_case_to_camel('the_snake_is_green', upper_case_first=False) == 'theSnakeIsGreen'

    assert reverse('hello') == 'olleh'

    shuffled = shuffle('hello world')
    assert sorted(shuffled) == sorted('hello world')

    assert strip_html('test: <a href="foo/bar">click here</a>') == 'test: '
    assert strip_html('test: <a href="foo/bar">click here</a>', keep_tag_content=True) == 'test: click here'

    assert prettify(' unprettified string ,, like this one,will be"prettified" .it\' s awesome! ') == \
        'Unprettified string, like this one, will be "prettified". It\'s awesome!'

    assert asciify('èéùúòóäåëýñÅÀÁÇÌÍÑÓË') == 'eeuuooaaeynAAACIINOE'

    assert slugify('Top 10 Reasons To Love Dogs!!!') == 'top-10-reasons-to-love-dogs'
    assert slugify('Mönstér Mägnët') == 'monster-magnet'

    assert booleanize('true') is True
    assert booleanize('YES') is True
    assert booleanize('nope') is False

    assert strip_margin('   line 1\n   line 2') == 'line 1\nline 2'


def test_compress_and_roman():
    original = ' '.join(['word n{}'.format(n) for n in range(20)])
    compressed = compress(original)
    assert len(compressed) < len(original)
    assert decompress(compressed) == original

    assert roman_encode(38) == 'XXXVIII'
    assert roman_encode(37) == 'XXXVII'
    assert roman_encode('2020') == 'MMXX'
    assert roman_decode('VII') == 7

    assert list(roman_range(7)) == ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
    assert list(roman_range(start=7, stop=1, step=-1)) == ['VII', 'VI', 'V', 'IV', 'III', 'II', 'I']

    for bad in (0, 4000):
        try:
            roman_encode(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('ValueError was not raised for {}'.format(bad))


def test_generation():
    value = uuid()
    assert is_uuid(value) is True
    assert uuid_module.UUID(value).version == 4
    assert is_uuid(uuid(as_hex=True), allow_hex=True) is True
    assert len(uuid(as_hex=True)) == 32

    text = random_string(9)
    assert len(text) == 9
    assert re.match(r'^[A-Za-z0-9]+$', text) is not None

    hex_value = secure_random_hex(9)
    assert len(hex_value) == 18
    assert re.match(r'^[0-9a-f]+$', hex_value) is not None

    for bad in (0, -1):
        for call in (lambda: random_string(bad), lambda: secure_random_hex(bad)):
            try:
                call()
            except ValueError:
                pass
            else:
                raise AssertionError('ValueError was not raised for {}'.format(bad))


def _called_name(call):
    func = call.func
    return func.id if isinstance(func, ast.Name) else getattr(func, 'attr', '')


def test_package_dependencies():
    # setup.py declares no runtime dependency
    with open(os.path.join(ROOT, 'setup.py'), encoding='utf-8') as f:
        tree = ast.parse(f.read())
    setup_call = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and _called_name(n) == 'setup']
    assert setup_call, 'setup() call not found'
    keywords = [kw.arg for kw in setup_call[0].keywords]
    assert 'install_requires' not in keywords

    # every module of the package imports only the standard library or the package itself
    stdlib = set(getattr(sys, 'stdlib_module_names', ()))
    assert stdlib, 'sys.stdlib_module_names is not available'
    package_dir = os.path.join(ROOT, 'string_utils')
    for filename in sorted(os.listdir(package_dir)):
        if not filename.endswith('.py'):
            continue
        with open(os.path.join(package_dir, filename), encoding='utf-8') as f:
            module = ast.parse(f.read())
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                names = [alias.name.split('.')[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module.split('.')[0]]
            else:
                continue
            for name in names:
                assert name in stdlib, '{} imports {}'.format(filename, name)


def test_credit_card_check():
    # known card types, with and without the type
    assert is_credit_card('4111111111111111') is True
    assert is_credit_card('4111111111111111', 'VISA') is True
    assert is_credit_card('4111111111111111', 'MASTERCARD') is False
    assert is_credit_card('5555555555554444', 'MASTERCARD') is True
    assert is_credit_card('378282246310005', 'AMERICAN_EXPRESS') is True
    assert is_credit_card('30569309025904', 'DINERS_CLUB') is True
    assert is_credit_card('6011111111111117', 'DISCOVER') is True
    assert is_credit_card('3530111333300000', 'JCB') is True
    assert is_credit_card('1234567890') is False

    # empty, blank and non-string input is False
    assert is_credit_card('') is False
    assert is_credit_card('   ') is False
    assert is_credit_card(None) is False
    assert is_credit_card(4111111111111111) is False

    # an unknown card type raises KeyError
    try:
        is_credit_card('4111111111111111', 'UNKNOWN_CARD')
    except KeyError:
        pass
    else:
        raise AssertionError('KeyError was not raised')
