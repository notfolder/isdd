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

from __future__ import division

from decimal import ROUND_HALF_UP, Decimal




def prefix_currency(prefix, base):
    return tuple("%s %s" % (prefix, i) for i in base)


def parse_currency_parts(value, is_int_with_cents=True):
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
    if isinstance(value, int):
        negative = value < 0
        absolute = abs(value)
        if is_int_with_cents:
            integer, cents = divmod(absolute, 100)
        else:
            integer, cents = absolute, 0
        return integer, cents, negative

    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    quantized = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    negative = quantized < 0
    absolute = abs(quantized)
    integer = int(absolute)
    cents = int((absolute - integer) * 100)
    return integer, cents, negative
