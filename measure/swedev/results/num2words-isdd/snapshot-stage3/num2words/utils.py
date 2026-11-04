# -*- coding: utf-8 -*-
# Copyright (c) 2003, Taro Ogawa.  All Rights Reserved.
# Copyright (c) 2013, Savoir-faire Linux inc.  All Rights Reserved.

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA




def splitbyx(n, x, format_int=True):
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
    length = len(n)
    if length > x:
        start = length % x
        if start > 0:
            chunk = n[:start]
            yield int(chunk) if format_int else chunk
        for i in range(start, length, x):
            chunk = n[i:i + x]
            yield int(chunk) if format_int else chunk
    else:
        yield int(n) if format_int else n


def get_digits(n):
    a = [int(x) for x in reversed(list(('%03d' % n)[-3:]))]
    return a
