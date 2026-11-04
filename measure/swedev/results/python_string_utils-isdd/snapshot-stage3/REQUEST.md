# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: python_string_utils-test_roman_encode

# FOLDER STRUCTURE:
```
..
└── string_utils/
    └── manipulation.py
        ├── __RomanNumbers.encode
        └── roman_encode
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module is a dedicated test suite designed to validate the functionality of a Roman numeral encoding utility. Its primary purpose is to ensure the correctness of the `roman_encode` function, which converts numeric values into their Roman numeral representations. The module provides extensive test cases that cover a wide range of inputs, including valid integers, string-based numeric inputs, and various edge cases such as invalid, decimal, or negative numbers. Through comprehensive assertion checks, it ensures that the encoding logic adheres to the expected behavior and handles errors appropriately. This module solves the problem of verifying the reliability and robustness of the Roman numeral conversion logic, offering developers confidence in its accuracy for integration or end-user use cases.

## FILE 1: string_utils/manipulation.py

- FUNCTION NAME: roman_encode
  - SIGNATURE: def roman_encode(input_number: Union[str, int]) -> str:
  - DOCSTRING: 
```python
"""
Convert a positive integer or a string representation of an integer (within the range 1-3999) into its corresponding Roman numeral string.

This function relies on the `__RomanNumbers` class, which encapsulates the encoding logic for Roman numerals. The encoding process uses predefined mappings for units, tens, hundreds, and thousands, ensuring that the return value adheres to Roman numeral conventions.

Parameters:
- input_number (Union[str, int]): A positive integer or a string that represents a positive integer to be converted into a Roman numeral.

Returns:
- str: The corresponding Roman numeral as a string.

Raises:
- ValueError: If the input is not a positive integer or is outside the specified range.

Examples:
>>> roman_encode(37)  # returns 'XXXVIII'
>>> roman_encode('2020')  # returns 'MMXX'
"""
```
  - DEPENDENCIES:
    - string_utils/manipulation.py:__RomanNumbers:encode

- CLASS METHOD: __RomanNumbers.encode
  - CLASS SIGNATURE: class __RomanNumbers:
  - SIGNATURE: def encode(cls, input_number: Union[str, int]) -> str:
  - DOCSTRING: 
```python
"""
Converts a given integer or string representing a positive integer (between 1 and 3999 inclusive) into its corresponding Roman numeral representation.

Parameters:
- input_number (Union[str, int]): A positive integer or string that can be parsed as an integer, which will be converted to a Roman numeral. Only integers within the range of 1 to 3999 are valid inputs.

Returns:
- str: The Roman numeral equivalent of the input number as a string.

Raises:
- ValueError: If the input is not a valid integer string or an integer, or if it falls outside the valid range (1 to 3999).

Dependencies:
- The method relies on the helper method `__encode_digit()` to convert individual digits based on predefined mappings found in `__mappings`, which are class-level constants that define the Roman numeral symbols for units, tens, hundreds, and thousands.
- The function also utilizes the `is_integer()` validation method to ensure the input is indeed an integer before conversion.
"""
```

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
