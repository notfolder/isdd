# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: num2words-test_utils

# FOLDER STRUCTURE:
```
..
└── num2words/
    └── utils.py
        └── splitbyx
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module provides utility functions for processing and segmenting numerical strings into smaller parts based on a specified length. Its primary functionality centers on converting a string representation of a number into distinct chunks that can either be returned as integers or preserved as strings, depending on the user's requirements. This enables developers to handle large numerical values efficiently in applications where localized or segmented numerical processing is essential, such as in formatting, data validation, or localized number representation systems. By abstracting the complexity of numeric segmentation, the module streamlines workflows for developers, improving code clarity and minimizing errors when handling numeric string manipulations.

## FILE 1: num2words/utils.py

- FUNCTION NAME: splitbyx
  - SIGNATURE: def splitbyx(n, x, format_int=True):
  - DOCSTRING: 
```python
"""
Splits a numeric string `n` into chunks of length `x`. If the length of `n` is greater than `x`, the function yields the initial segment that is shorter than `x`, followed by subsequent segments of length `x`. The results can be returned as integers or strings based on the `format_int` parameter.

Parameters:
- n (str): The numeric string to be split.
- x (int): The length of each chunk to split the string into.
- format_int (bool): If True (default), yields the results as integers; if False, yields them as strings.

Yields:
- int or str: Each chunk of the numeric string as specified by `format_int`.

Note: The function uses Python's `yield` statement for generating results as a sequence, enabling iteration over the yielded values.
"""
```

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
