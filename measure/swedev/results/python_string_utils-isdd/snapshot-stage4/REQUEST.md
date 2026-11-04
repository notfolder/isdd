# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: python_string_utils-test_uuid

# FOLDER STRUCTURE:
```
..
└── string_utils/
    ├── generation.py
    │   └── uuid
    └── validation.py
        └── is_uuid
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module facilitates the validation and generation of UUIDs, ensuring compatibility with systems or features requiring unique identifiers. It provides functionality to create UUID strings in both standard UUID format and hexadecimal representation, along with verification to confirm whether a given string conforms to the UUID specification. By automating and standardizing UUID generation and validation, the module reduces the risk of errors in identifier handling, streamlines development workflows, and supports developers in ensuring data integrity and compliance with UUID-related requirements.

## FILE 1: string_utils/validation.py

- FUNCTION NAME: is_uuid
  - SIGNATURE: def is_uuid(input_string: Any, allow_hex: bool=False) -> bool:
  - DOCSTRING: 
```python
"""
Check if a string is a valid UUID (Universally Unique Identifier).

This function validates whether the input string matches the UUID format as defined by the RFC 4122 standard. It also provides the option to allow hex representation of UUIDs.

Parameters:
- input_string (Any): The string to check for UUID validity. It is cast to a string if it is not already one.
- allow_hex (bool): If True, permits hexadecimal representation of UUIDs as valid. Defaults to False.

Returns:
- bool: True if the string is a valid UUID, false otherwise.

Dependencies:
- UUID_RE: A regular expression constant that matches the standard UUID format.
- UUID_HEX_OK_RE: A regular expression constant that matches the hex representation of UUIDs. Both are defined in the imported module containing regular expressions for various validations.
"""
```

## FILE 2: string_utils/generation.py

- FUNCTION NAME: uuid
  - SIGNATURE: def uuid(as_hex: bool=False) -> str:
  - DOCSTRING: 
```python
"""
Generates a UUID string using the `uuid.uuid4()` function.

This function can return the UUID in its standard format (e.g., '97e3a716-6b33-4ab9-9bb1-8128cb24d76b') or as a hexadecimal string (e.g., '97e3a7166b334ab99bb18128cb24d76b') based on the `as_hex` parameter.

Parameters:
- as_hex (bool): If set to True, the function returns the UUID in hexadecimal format. Defaults to False.

Returns:
- str: A string representation of the generated UUID, either in standard format or hexadecimal format based on the `as_hex` parameter.

Dependencies:
- This function relies on the `uuid4` method from the `uuid` module to generate a unique identifier.
"""
```

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
