# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: python_string_utils-test_strip_html

# FOLDER STRUCTURE:
```
..
└── string_utils/
    ├── errors.py
    │   └── InvalidInputError.__init__
    ├── manipulation.py
    │   └── strip_html
    └── validation.py
        └── is_string
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module facilitates the sanitization of strings by removing HTML tags while providing the flexibility to optionally retain the textual content within those tags. Its core functionality ensures that input data is cleaned and devoid of any unwanted HTML markup, making it suitable for further processing, display, or storage in plain-text formats. Key features include robust handling of multiple HTML tags, the ability to preserve non-tag content within the HTML structure if specified, and comprehensive type safety to ensure only valid string inputs are processed. This module addresses the common challenge of safely extracting or cleaning text data from HTML-encoded content, enabling developers to preprocess user inputs or web-scraped data efficiently and securely.

## FILE 1: string_utils/manipulation.py

- FUNCTION NAME: strip_html
  - SIGNATURE: def strip_html(input_string: str, keep_tag_content: bool=False) -> str:
  - DOCSTRING: 
```python
"""
Remove HTML tags from the provided string.

This function processes the input string to eliminate HTML tags, returning either the plain text or the text with the content of the tags preserved based on the `keep_tag_content` parameter. It raises an `InvalidInputError` if the input is not a valid string. The function uses the `HTML_TAG_ONLY_RE` regular expression to remove tags while keeping their content if `keep_tag_content` is `True`, and `HTML_RE` to remove both tags and their content if `False`. These regular expressions are defined elsewhere in the codebase and facilitate the manipulation of strings containing HTML.

:param input_string: The input string containing potential HTML code.
:type input_string: str
:param keep_tag_content: Flag to indicate whether to preserve content within HTML tags (default is False).
:type keep_tag_content: bool
:return: A string with HTML removed or preserved based on the `keep_tag_content` parameter.
:rtype: str
"""
```
  - DEPENDENCIES:
    - string_utils/errors.py:InvalidInputError:__init__
    - string_utils/validation.py:is_string

## FILE 2: string_utils/errors.py

- CLASS METHOD: InvalidInputError.__init__
  - CLASS SIGNATURE: class InvalidInputError(TypeError):
  - SIGNATURE: def __init__(self, input_data: Any):
  - DOCSTRING: 
```python
"""
Initializes an instance of the InvalidInputError class, which is a custom error type raised when an input is not of the expected string type. 

Parameters:
- input_data (Any): The object received by the error, which is checked against the expected type. 

The constructor retrieves the type of the received input_data using Python's built-in type function and constructs a descriptive error message that indicates the expected type ("str") and the actual type received. It then calls the superclass constructor to initialize the error message in the TypeError base class. 

This method does not return a value but raises an exception with a custom message when the input data type is incorrect.
"""
```

## FILE 3: string_utils/validation.py

- FUNCTION NAME: is_string
  - SIGNATURE: def is_string(obj: Any) -> bool:
  - DOCSTRING: 
```python
"""
Checks if the given object is an instance of a string.

The function is part of a utilities module that provides various validation schemes, where `is_string` serves as a foundational check to determine whether an object can be treated as a string. 

Parameters:
- obj (Any): The input object to be tested.

Returns:
- bool: True if the object is a string, otherwise False.

This function is invoked in various other functions throughout the module, such as `is_full_string`, `is_number`, and `contains_html`, ensuring type safety by confirming that the inputs are of the expected type before performing further validation operations. It specifically guards against erroneous inputs that may cause exceptions during type-specific operations.
"""
```
  - DEPENDENCIES:
    - string_utils/manipulation.py:strip_html

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
