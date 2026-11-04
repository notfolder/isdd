# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: yamllint-test_anchors

# FOLDER STRUCTURE:
```
..
└── yamllint/
    ├── linter.py
    │   ├── LintProblem.__eq__
    │   ├── LintProblem.__init__
    │   ├── LintProblem.__lt__
    │   ├── _run
    │   └── run
    └── parser.py
        └── Comment.Comment
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module is designed to validate and enforce rules around the usage of anchors and aliases in YAML documents, ensuring compliance with specified configurations. It provides capabilities to detect and optionally forbid issues such as undeclared aliases, duplicated anchors, and unused anchors, offering configurable settings for each rule. By automating the identification of these potential problems, the module helps developers maintain clean, consistent, and error-free YAML structures, reducing the risk of misconfigurations and improving the reliability of YAML-based workflows. This functionality is particularly useful for teams managing complex YAML files or adhering to strict style guidelines.

## FILE 1: yamllint/linter.py

- FUNCTION NAME: run
  - SIGNATURE: def run(input, conf, filepath=None):
  - DOCSTRING: 
```python
"""
Lints a YAML source and identifies potential problems using the yamllint configuration.

This function checks the provided YAML input for syntax errors and cosmetic issues according to the `yamllint` rules. It returns a generator that yields instances of `LintProblem`, which encapsulate the details of any detected problems.

Parameters:
- input: A buffer, string, or stream to read from containing the YAML source.
- conf: A configuration object specific to `yamllint`, which defines the linting rules and their statuses.
- filepath: An optional string representing the file path of the input, used to check if the file is ignored by the configuration.

Returns:
- A generator of `LintProblem` objects representing any linting issues or syntax errors found in the input. If the file is ignored or if the input is of unsupported type, appropriate handling is performed.

Dependencies:
- This function relies on the `_run` function to process the input and the `get_cosmetic_problems` function to identify linting issues. Additionally, it interacts with `io` for reading from stream inputs and uses `yaml` for parsing YAML content.
"""
```
  - DEPENDENCIES:
    - tests/common.py:RuleTestCase:check

- CLASS METHOD: LintProblem.__init__
  - CLASS SIGNATURE: class LintProblem:
  - SIGNATURE: def __init__(self, line, column, desc='<no description>', rule=None):
  - DOCSTRING: 
```python
"""
Initializes a LintProblem instance, representing a linting issue found in a YAML document.

Parameters:
- line (int): The line number where the problem was found, starting at 1.
- column (int): The column number where the problem was found, starting at 1.
- desc (str, optional): A human-readable description of the problem. Defaults to '<no description>'.
- rule (str, optional): The identifier of the rule that detected the problem. Defaults to None.

Attributes:
- line (int): Stores the line number of the problem.
- column (int): Stores the column number of the problem.
- desc (str): Stores the description of the problem.
- rule (str): Stores the identifier of the rule that indicated the problem.
- level (int or None): Initialized as None, intended to represent the severity level of the linting problem.

This class is used in conjunction with linting rules defined elsewhere in the code, allowing it to capture and represent specific issues detected during YAML linting.
"""
```

- CLASS METHOD: LintProblem.__lt__
  - CLASS SIGNATURE: class LintProblem:
  - SIGNATURE: def __lt__(self, other):
  - DOCSTRING: 
```python
"""
Determines the ordering of LintProblem instances based on their line and column attributes.

This method compares two LintProblem objects, `self` and `other`, to establish their relative order. It first compares the `line` attribute; if they are equal, it then compares the `column` attribute. The purpose of this method is to enable sorting of linting problems based on their position in the YAML document, making it easier to organize and display them.

Parameters:
- other (LintProblem): The other LintProblem instance to compare against.

Returns:
- bool: True if `self` is less than `other` in terms of line and column, otherwise False.

This method interacts with the `line` and `column` attributes of the LintProblem class, which are defined in its constructor. These attributes are crucial for identifying the location of linting issues in the source YAML.
"""
```

- CLASS METHOD: LintProblem.__eq__
  - CLASS SIGNATURE: class LintProblem:
  - SIGNATURE: def __eq__(self, other):
  - DOCSTRING: 
```python
"""
Checks for equality between two LintProblem instances.

Parameters:
- other (LintProblem): Another instance of LintProblem to compare against.

Returns:
- bool: True if both instances represent the same lint problem (same line, column, and rule); False otherwise.

This method is important for determining if two LintProblem objects represent the same issue in YAML linting, allowing for proper aggregation and handling of unique linting problems.
"""
```

- FUNCTION NAME: _run
  - SIGNATURE: def _run(buffer, conf, filepath):
  - DOCSTRING: 
```python
"""
Runs the YAML linting process on a provided buffer, checking for syntax errors and generating cosmetic problem reports.

Parameters:
- buffer: A string, bytes, or a buffer-like object containing the YAML content to lint.
- conf: A configuration object that defines linting rules and directives.
- filepath: An optional string representing the file path of the YAML document (used for rule application context).

Returns:
- A generator yielding LintProblem instances, which encapsulate linting issues found in the YAML source.

Dependencies:
- The function uses the `get_syntax_error` function to check for syntax errors and `get_cosmetic_problems` to identify stylistic issues.
- If the content includes a disable-file directive on the first line, linting is skipped.
- The function asserts that the input buffer supports indexing, as it requires access to specific lines of the input.

Side Effects:
- The function can yield a syntax error if present, immediately prioritizing it over cosmetic problems to prevent redundancy in output.
"""
```
  - DEPENDENCIES:
    - tests/common.py:RuleTestCase:check
    - yamllint/parser.py:Line:content
    - yamllint/parser.py:line_generator
    - yamllint/linter.py:get_cosmetic_problems
    - yamllint/linter.py:get_syntax_error

## FILE 2: yamllint/parser.py

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
