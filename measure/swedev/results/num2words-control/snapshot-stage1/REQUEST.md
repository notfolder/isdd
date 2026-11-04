# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: num2words-test_currency

# FOLDER STRUCTURE:
```
..
└── num2words/
    └── currency.py
        └── parse_currency_parts
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module provides functionality for parsing and processing numeric currency values into their constituent parts for precise financial calculations and representations. It supports various input formats, including integers, floats, decimal objects, and strings, and extracts data such as whole currency units, fractional cents, and whether the amount is negative. This capability ensures accurate decomposition of currency values, facilitating use cases like formatting, reconciling, or validating monetary data in financial and accounting systems. By standardizing currency parsing, the module addresses the complexities of handling diverse numeric inputs and rounding behaviors, offering developers a reliable tool for consistent currency manipulations.

## FILE 1: num2words/currency.py

- FUNCTION NAME: parse_currency_parts
  - SIGNATURE: def parse_currency_parts(value, is_int_with_cents=True):
  - DOCSTRING: 
```python
"""
Parses a currency value into its integer and cents components, along with a sign indicator.

Parameters:
    value (int or str or Decimal): The value to parse, which can be an integer representing cents or a string/Decimal to represent currency.
    is_int_with_cents (bool): A flag to determine whether an integer value should be treated as having cents (default is True).

Returns:
    tuple: A tuple containing three elements:
        - integer (int): The integer part of the currency value.
        - cents (int): The fractional part of the currency value in cents.
        - negative (bool): A boolean indicating if the original value was negative.

This function uses the `Decimal` class from the `decimal` module to ensure accurate monetary calculations, and employs the `ROUND_HALF_UP` constant for rounding behavior when quantizing the value to two decimal places.
"""
```

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
