# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: yamllint-test_indentation

# FOLDER STRUCTURE:
```
..
└── yamllint/
    ├── parser.py
    │   ├── Comment.Comment
    │   └── token_or_comment_generator
    └── rules/
        └── indentation.py
            ├── Parent.__repr__
            └── check
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module is designed to validate and enforce indentation consistency and formatting rules within YAML documents. Its primary functionality is to ensure compliance with predefined indentation configurations, such as the number of spaces, sequence alignment, and multi-line string formatting. It supports advanced validations, such as detecting inconsistent spaces, over-indentation, under-indentation, and proper alignment for nested structures, including maps, sequences, and flow collections. This module addresses the problem of YAML misalignment and syntax errors, providing developers with a tool to maintain standardized and readable YAML files, which is critical for configuration management, automation pipelines, and overall reliability in YAML-based workflows.

## FILE 1: yamllint/parser.py

- FUNCTION NAME: token_or_comment_generator
  - SIGNATURE: def token_or_comment_generator(buffer):
  - DOCSTRING: 
```python
"""
Generates tokens and comments from a given YAML buffer.

Parameters:
- buffer (str): A string containing the YAML content to be processed.

Returns:
- Yields a Token object for each token found in the buffer, which includes the current token, its previous and next tokens, and the next-next token. Additionally, it yields Comment objects for comments found between the tokens.

Dependencies:
- This function relies on the `yaml` module, specifically `yaml.BaseLoader`, to parse the YAML content and retrieve tokens. It interacts with the `comments_between_tokens` function to extract comments related to the tokens.
- The `Token` class is used to encapsulate the structure of each token, while the `Comment` class is utilized to manage comment details. The method `get_token()` from the `yaml_loader` retrieves tokens one at a time, and `check_token()` and `peek_token()` are used to manage the flow of token extraction.
"""
```
  - DEPENDENCIES:
    - yamllint/parser.py:Token:__init__
    - yamllint/parser.py:comments_between_tokens

## FILE 2: yamllint/rules/indentation.py

- FUNCTION NAME: check
  - SIGNATURE: def check(conf, token, prev, next, nextnext, context):
  - DOCSTRING: 
```python
"""
Validate the indentation of YAML tokens based on specified formatting rules.

Parameters:
- conf (dict): Configuration dictionary containing indentation settings. It includes:
  - 'spaces' (int or str): Defines indentation width, can be a specific number of spaces or 'consistent'.
  - 'indent-sequences' (bool or str): Controls whether block sequences should be indented.
  - 'check-multi-line-strings' (bool): Specifies if indentation in multi-line strings should be checked.
- token (yaml.Token): The current YAML token being processed.
- prev (yaml.Token): The previous token for context during validation.
- next (yaml.Token): The next token, used for forward context.
- nextnext (yaml.Token): The token after next, for further context in validation.
- context (dict): Dictionary maintaining the current state, including:
  - 'stack' (list): Tracks the indentation levels during parsing.
  - 'cur_line' (int): The current line being processed.
  - 'spaces' (int or str): The configured spaces setting.

Returns:
- generator: Yields LintProblem instances if any indentation issues are found, or asserts if a state inconsistency occurs.

This function interacts with the `_check` function to lint indentation and handles exceptions gracefully, yielding appropriate problems when unexpected tokens are detected.
"""
```
  - DEPENDENCIES:
    - yamllint/rules/indentation.py:_check

- CLASS METHOD: Parent.__repr__
  - CLASS SIGNATURE: class Parent:
  - SIGNATURE: def __repr__(self):
  - DOCSTRING: 
```python
"""
Return a string representation of the Parent instance, displaying its type and indentation level.

The method uses a constant tuple `labels`, which maps integer values representing different types of YAML structure (defined in the surrounding code) to their corresponding string names. The `self.type` attribute is indexed in `labels` to obtain this string, while `self.indent` provides the indentation level of the current instance. The output format is `"{label}:{indent}"`, which allows for clarity in identifying the type of YAML structure associated with this Parent instance.

Returns:
    str: A string indicating the type and indentation of the Parent instance.
"""
```

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
