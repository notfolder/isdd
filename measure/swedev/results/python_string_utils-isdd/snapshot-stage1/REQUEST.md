# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: python_string_utils-test_is_credit_card

# FOLDER STRUCTURE:
```
..
└── string_utils/
    └── validation.py
        └── is_credit_card
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module is designed to validate whether a given string is a valid credit card number and optionally verify its adherence to a specified card type. It supports multiple card providers, including VISA, MasterCard, Discover, American Express, JCB, and Diners Club, ensuring comprehensive coverage for common card types. The module provides functionality to handle various input edge cases, such as non-string inputs, invalid formats, or unsupported card types, enhancing robustness in card validation. By offering precise and reliable credit card validation, this module simplifies identifying and filtering valid card numbers for developers, reducing implementation errors and improving the security of applications that process credit card information.

## FILE 1: string_utils/validation.py

- FUNCTION NAME: is_credit_card
  - SIGNATURE: def is_credit_card(input_string: Any, card_type: str=None) -> bool:
  - DOCSTRING: 
```python
"""
Checks if a given string is a valid credit card number. It can validate against a specific card type (such as VISA, MASTERCARD, etc.) if provided; otherwise, it returns true for any valid credit card type from the predefined known types.

:param input_string: The string representation of the credit card number to check.
:type input_string: str
:param card_type: An optional parameter specifying the type of credit card to validate against. Default is None, allowing for any known card type.
:type card_type: str
:return: True if the credit card number is valid, false otherwise.

This function relies on the `CREDIT_CARDS` constant, which is a dictionary containing regex patterns for different credit card types, facilitating type-specific validation. If the `card_type` is not found in `CREDIT_CARDS`, a KeyError is raised. The function first checks if the input is a non-empty string; if not, it returns false.
"""
```
  - DEPENDENCIES:
    - string_utils/validation.py:is_full_string

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
