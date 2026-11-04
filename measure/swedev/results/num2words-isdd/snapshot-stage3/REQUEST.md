# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

# PROJECT NAME: num2words-test_base

# FOLDER STRUCTURE:
```
..
└── num2words/
    └── base.py
        ├── Num2Word_Base.__init__
        ├── Num2Word_Base.merge
        ├── Num2Word_Base.pluralize
        ├── Num2Word_Base.set_high_numwords
        ├── Num2Word_Base.title
        ├── Num2Word_Base.to_cardinal_float
        ├── Num2Word_Base.to_currency
        └── Num2Word_Base.to_ordinal_num
```

# IMPLEMENTATION REQUIREMENTS:
## MODULE DESCRIPTION:
The module provides a foundational framework for converting numerical values into language-based representations, designed to support the development of multilingual or locale-specific number-to-word conversion functionalities. It defines a base class, `Num2Word_Base`, which outlines core methods such as converting numbers to ordinals, cardinals, or currency representations, while also allowing for customization like title formatting and pluralization rules. By offering a structured interface and robust error handling around unimplemented or unsupported features, it ensures extensibility and serves as a reliable backbone for developers implementing specific or localized number-to-word conversion logic. This module addresses the challenge of creating consistent, reusable, and testable mechanisms for linguistic number representation, streamlining the process for applications requiring this functionality.

## FILE 1: num2words/base.py

- CLASS METHOD: Num2Word_Base.to_cardinal_float
  - CLASS SIGNATURE: class Num2Word_Base(object):
  - SIGNATURE: def to_cardinal_float(self, value):
  - DOCSTRING: 
```python
"""
Converts a float number into its cardinal representation as a string. The function handles both the integer and fractional parts of the number. It first verifies that the input is a numeric type, and then separates the number into its whole and decimal components using the `float2tuple` method. The whole part is converted to its cardinal form using the `to_cardinal` method, and the fractional part is formatted according to the specified precision.

Parameters:
- value (float): The numeric value to be converted into cardinal form.

Returns:
- str: A string representation of the number in cardinal form, including the fractional part if applicable.

Dependencies:
- The method depends on `self.float2tuple` for separating the integer and decimal parts and `self.to_cardinal` for converting numbers to their cardinal representations. It also uses `self.title` for formatting titles and `self.precision`, which defines the number of decimal places to consider.
"""
```

- CLASS METHOD: Num2Word_Base.pluralize
  - CLASS SIGNATURE: class Num2Word_Base(object):
  - SIGNATURE: def pluralize(self, n, forms):
  - DOCSTRING: 
```python
"""
Resolve plural forms based on the given count 'n' and the specified 'forms'.

Args:
    n (int): The numeric value that determines which form to return.
    forms (list): A list of string forms for singular and plural representations, 
                  typically containing at least two elements: the singular form 
                  at index 0 and the plural form at index 1.

Returns:
    str: The appropriate form based on the value of 'n'. If 'n' is 1, the 
         singular form is returned; otherwise, the plural form is returned.

Note:
    The method is marked as NotImplementedError; it requires an implementation 
    specific to how pluralization should be handled in the derived classes.
"""
```

- CLASS METHOD: Num2Word_Base.set_high_numwords
  - CLASS SIGNATURE: class Num2Word_Base(object):
  - SIGNATURE: def set_high_numwords(self, *args):
  - DOCSTRING: 
```python
"""
Sets the high number words used for cardinal number conversion in the Num2Word_Base class.

Parameters:
    *args: Variable length argument list that should typically contain high number words.

Returns:
    None. This method is intended to be overridden in subclasses to provide specific implementations for high number words.

Raises:
    NotImplementedError: This is a placeholder method meant to be implemented in derived classes, allowing for different languages or number representations.

This method interacts with the overall conversion system of cardinal numbers to words by preparing a set of high number words which will be used in the conversion logic defined in the Num2Word_Base class and its derived classes.
"""
```

- CLASS METHOD: Num2Word_Base.title
  - CLASS SIGNATURE: class Num2Word_Base(object):
  - SIGNATURE: def title(self, value):
  - DOCSTRING: 
```python
"""
Convert the given string value to title case if the `is_title` attribute is set to True.

Parameters:
    value (str): A string that may contain multiple words.

Returns:
    str: The input string converted to title case, where each word starts with an uppercase letter, 
          except for words present in the `exclude_title` list, which remain unchanged.

Notes:
    - The `is_title` attribute controls whether the title case transformation is applied.
    - The `exclude_title` attribute is a list of words that should not be capitalized.
    - This method contributes to the overall functionality of the `Num2Word_Base` class by allowing
      formatted output for numerical words, ensuring proper capitalization based on context.
"""
```

- CLASS METHOD: Num2Word_Base.__init__
  - CLASS SIGNATURE: class Num2Word_Base(object):
  - SIGNATURE: def __init__(self):
  - DOCSTRING: 
```python
"""
Initialize a Num2Word_Base instance, setting up essential attributes for converting numerical values into words. This constructor initializes the following attributes:

- `is_title`: A boolean indicating if the output should be title-cased.
- `precision`: An integer representing the number of decimal places to consider, defaulting to 2.
- `exclude_title`: A list of words to exclude from title casing.
- `negword`: A string representing the symbol for negative numbers.
- `pointword`: A string representing the symbol for decimal points.
- `errmsg_nonnum`, `errmsg_floatord`, `errmsg_negord`, `errmsg_toobig`: Strings used for error messages for various exceptional cases.

After setting these attributes, the `setup()` method is called to perform any necessary initialization. If the instance has attributes related to number words (`high_numwords`, `mid_numwords`, `low_numwords`), it initializes an `OrderedDict` for cardinal numbers (`cards`) and calculates `MAXVAL` based on the highest numerical key available.

Constants such as `self.negword` and `self.pointword` provide standard representations of negative and decimal values, respectively, which are crucial for formatting output correctly. The initialization ensures the instance is ready to convert numbers into their corresponding verbal forms, preparing values for further processing in methods that handle numerical conversions.
"""
```

- CLASS METHOD: Num2Word_Base.to_ordinal_num
  - CLASS SIGNATURE: class Num2Word_Base(object):
  - SIGNATURE: def to_ordinal_num(self, value):
  - DOCSTRING: 
```python
"""
Convert a numeric value to its ordinal representation. 

Args:
    value (int or float): The numeric value to be converted to an ordinal number. 

Returns:
    int or float: The input value unchanged; this method currently serves as a placeholder or trivial implementation.

Note:
    This method does not perform any conversion or processing; it simply returns the input value as is. It is intended to be overridden in subclasses that implement specific ordinal formatting.
"""
```

- CLASS METHOD: Num2Word_Base.merge
  - CLASS SIGNATURE: class Num2Word_Base(object):
  - SIGNATURE: def merge(self, curr, next):
  - DOCSTRING: 
```python
"""
Merges two numerical components into a single representation.

Args:
    curr: The first component to merge, expected to be a tuple 
          containing numerical representations.
    next: The second component to merge, also expected to be a 
          tuple containing numerical representations.

Returns:
    NotImplementedError: This method must be implemented in a derived 
    class as it serves as a placeholder for custom merging logic 
    specific to the subclass's requirements.

This method is essential for the `clean` method, which processes 
numerical representations. The merging logic is expected to provide 
meaningful combinations of numerical parts based on the context of 
usage, such as combining different levels of cardinal numbers or 
handling special cases in numbering formats.
"""
```

- CLASS METHOD: Num2Word_Base.to_currency
  - CLASS SIGNATURE: class Num2Word_Base(object):
  - SIGNATURE: def to_currency(self, val, currency='EUR', cents=True, separator=',', adjective=False):
  - DOCSTRING: 
```python
"""
Converts a numeric value to a currency string formatted according to specified parameters.

Args:
    val (numeric): The numeric value to format as currency.
    currency (str): The currency code (default is 'EUR'). It is used to determine the appropriate currency formatting. Should correspond to keys in the CURRENCY_FORMS dictionary.
    cents (bool): If True, formats the cents in a verbose manner; if False, formats them tersely (default is True).
    separator (str): The string used to separate the units from the cents (default is ',').
    adjective (bool): If True, prefixes the currency name with an adjective based on the CURRENCY_ADJECTIVES dictionary if available.

Returns:
    str: A formatted currency string that includes the appropriate adjective, monetary amount, and cents.

The method relies on the CURRENCY_FORMS dictionary, which maps currency codes to their respective formatted representations. Additionally, it uses the CURRENCY_ADJECTIVES for generating currency names with adjectives, if applicable. The method also calls _money_verbose and _cents_verbose (or _cents_terse) for custom formatting of monetary amounts and cents, respectively. If the currency code provided is not implemented, a NotImplementedError is raised.
"""
```

# TASK DESCRIPTION:
In this project, you need to implement the functions and methods listed above. The functions have been removed from the code but their docstrings remain.
Your task is to:
1. Read and understand the docstrings of each function/method
2. Understand the dependencies and how they interact with the target functions
3. Implement the functions/methods according to their docstrings and signatures
4. Ensure your implementations work correctly with the rest of the codebase
