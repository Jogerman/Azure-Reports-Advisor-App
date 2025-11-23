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
def intcomma(value, use_l10n=True):
    """
    Format a number with thousand separators (commas).
    Uses Django's proven humanize implementation.

    Usage in templates:
        {{ total_recommendations|intcomma }}
        {{ 26970|intcomma }}  -> "26,970"

    Args:
        value: The number to format (int, float, Decimal, or string)
        use_l10n: Use Django localization settings (default: True)

    Returns:
        A string with the number formatted with commas, or the original value if invalid
    """
    from django.contrib.humanize.templatetags.humanize import intcomma as django_intcomma

    try:
        if value is None or value == '':
            return value
        return django_intcomma(value, use_l10n=use_l10n)
    except (ValueError, TypeError, AttributeError):
        return value
