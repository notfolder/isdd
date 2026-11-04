from unittest import TestCase

from string_utils import is_credit_card


class IsCreditCardTestCase(TestCase):

    def test_should_return_false_for_non_string_objects(self):
        # noinspection PyTypeChecker
        self.assertFalse(is_credit_card(None))

        # noinspection PyTypeChecker
        self.assertFalse(is_credit_card(4111111111111111))

        # noinspection PyTypeChecker
        self.assertFalse(is_credit_card(b'4111111111111111'))

    def test_should_return_false_for_empty_or_blank_strings(self):
        self.assertFalse(is_credit_card(''))
        self.assertFalse(is_credit_card('   '))

    def test_should_validate_every_known_card_type_without_type(self):
        self.assertTrue(is_credit_card('4111111111111111'))  # VISA
        self.assertTrue(is_credit_card('4111111111111'))  # VISA (13 digits)
        self.assertTrue(is_credit_card('5555555555554444'))  # MASTERCARD
        self.assertTrue(is_credit_card('378282246310005'))  # AMERICAN_EXPRESS
        self.assertTrue(is_credit_card('30569309025904'))  # DINERS_CLUB
        self.assertTrue(is_credit_card('6011111111111117'))  # DISCOVER
        self.assertTrue(is_credit_card('3530111333300000'))  # JCB

    def test_should_return_false_for_unknown_numbers(self):
        self.assertFalse(is_credit_card('1234'))
        self.assertFalse(is_credit_card('abcd1111111111111'))
        self.assertFalse(is_credit_card('4111 1111 1111 1111'))

    def test_should_validate_against_the_given_card_type(self):
        self.assertTrue(is_credit_card('4111111111111111', 'VISA'))
        self.assertFalse(is_credit_card('4111111111111111', 'MASTERCARD'))
        self.assertTrue(is_credit_card('5555555555554444', 'MASTERCARD'))
        self.assertTrue(is_credit_card('378282246310005', 'AMERICAN_EXPRESS'))
        self.assertTrue(is_credit_card('30569309025904', 'DINERS_CLUB'))
        self.assertTrue(is_credit_card('6011111111111117', 'DISCOVER'))
        self.assertTrue(is_credit_card('3530111333300000', 'JCB'))

    def test_should_raise_key_error_for_unknown_card_type(self):
        with self.assertRaises(KeyError):
            is_credit_card('4111111111111111', 'UNKNOWN_CARD')
