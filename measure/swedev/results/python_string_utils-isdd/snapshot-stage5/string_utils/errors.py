# -*- coding: utf-8 -*-

from typing import Any


class InvalidInputError(TypeError):
    """
    Custom error raised when received object is not a string as expected.
    """

    def __init__(self, input_data: Any):
        """
        Initializes an instance of the InvalidInputError class, which is a custom error type raised when an input
        is not of the expected string type.

        Parameters:
        - input_data (Any): The object received by the error, which is checked against the expected type.

        The constructor builds a message naming the expected type ("str") and the type actually received, and
        passes it to the TypeError base class.
        """
        received_type = type(input_data).__name__
        TypeError.__init__(self, 'Expected "str", received "{}"'.format(received_type))

