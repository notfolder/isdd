# -*- coding: utf-8 -*-

from typing import Any


class InvalidInputError(TypeError):
    """
    Custom error raised when received object is not a string as expected.
    """

    def __init__(self, input_data: Any):
        super().__init__('Expected "str", received "{}"'.format(type(input_data).__name__))

