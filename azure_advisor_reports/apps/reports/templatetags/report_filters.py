"""
Custom template filters for reports.
"""

from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument.

    Usage in templates:
        {{ value|multiply:3 }}

    Args:
        value: The value to multiply (number)
        arg: The multiplier (number)

    Returns:
        The product of value * arg, or 0 if either is None/invalid
    """
    try:
        if value is None or arg is None:
            return 0

        # Convert to Decimal for precision with currency
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0


@register.filter
def intcomma(value):
    """
    Format a number with thousand separators (commas).

    Usage in templates:
        {{ total_recommendations|intcomma }}
        {{ 26970|intcomma }}  -> "26,970"

    Args:
        value: The number to format (int, float, Decimal, or string)

    Returns:
        A string with the number formatted with commas, or the original value if invalid
    """
    try:
        if value is None or value == '':
            return value

        # Convert to string and handle negative numbers
        orig = str(value)
        is_negative = orig.startswith('-')
        if is_negative:
            orig = orig[1:]

        # Split into integer and decimal parts
        parts = orig.split('.')
        int_part = parts[0]

        # Add commas to integer part
        # Reverse, group by 3, join with commas, reverse back
        int_part_with_commas = ','.join(
            int_part[::-1][i:i+3][::-1]
            for i in range(0, len(int_part), 3)
        )[::-1]

        # Reconstruct with decimal part if it exists
        result = int_part_with_commas
        if len(parts) > 1:
            result += '.' + parts[1]

        # Add negative sign back if needed
        if is_negative:
            result = '-' + result

        return result
    except (ValueError, TypeError, AttributeError):
        return value
