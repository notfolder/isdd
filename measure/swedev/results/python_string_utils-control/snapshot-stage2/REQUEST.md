# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: python_string_utils-test_is_ip_v4

# FOLDER STRUCTURE:
```
..
└── string_utils/
    └── validation.py
        ├── is_full_string
        └── is_ip_v4
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
This module is designed to validate and enforce correct formatting of IPv4 addresses by providing a suite of test cases for the `is_ip_v4` function. It ensures that the function accurately distinguishes valid IPv4 addresses from invalid inputs, such as non-string objects, improperly formatted or out-of-range addresses, and addresses containing extra spaces, invalid delimiters, or incorrect structures. By systematically testing edge cases and invalid scenarios, the module helps developers maintain robustness and correctness in applications that rely on IPv4 address validation. This improves reliability and reduces the likelihood of errors when processing or handling network-related inputs.

## FILE 1: string_utils/validation.py

- FUNCTION NAME: is_ip_v4
  - SIGNATURE: def is_ip_v4(input_string: Any) -> bool:
  - DOCSTRING: 
```python
"""
Checks if a given string is a valid IPv4 address.

An IPv4 address consists of four decimal numbers separated by dots, where each number ranges from 0 to 255. This function first verifies if the input string is a non-empty string and matches a shallow pattern defined by the `SHALLOW_IP_V4_RE` regular expression. It then checks each octet of the address to ensure they fall within the valid range.

:param input_string: The string representation of the potential IPv4 address to check.
:type input_string: Any
:return: True if the input string is a valid IPv4 address; False otherwise.

Dependencies:
- `is_full_string`: Checks if the string is not empty and contains meaningful characters.
- `SHALLOW_IP_V4_RE`: A regular expression pattern that is used to perform a preliminary check for the structure of the IPv4 address.
"""
```
  - DEPENDENCIES:
    - string_utils/validation.py:is_full_string

- FUNCTION NAME: is_full_string
  - SIGNATURE: def is_full_string(input_string: Any) -> bool:
  - DOCSTRING: 
```python
"""
Checks whether the provided input is a non-empty string that contains at least one non-space character. 

Parameters:
- input_string (Any): The input to check, expected to be of type str.

Returns:
- bool: True if input_string is a valid string and not empty (after stripping whitespace); False otherwise.

This function utilizes the `is_string` utility function from the same module to validate the type of input_string. It ensures that only valid string inputs are considered, filtering out None, empty strings, and strings that only contain whitespace.
"""
```
  - DEPENDENCIES:
    - string_utils/validation.py:is_ip_v4
    - string_utils/validation.py:is_string

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
