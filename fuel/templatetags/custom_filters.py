from django import template

register = template.Library()

@register.filter
def sum_attr(queryset, attr):
    return sum(getattr(item, attr) for item in queryset)

@register.filter
def div(value, arg):
    if value is None or arg is None:
        return 0  # or return an empty string, or any fallback value you'd prefer
    try:
        result = float(value) / float(arg)  # Simple division for price per liter calculation
        return round(result, 2)  # Round to 2 decimal places to avoid floating point precision issues
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (ValueError, TypeError):
        return 0
    
@register.filter
def sum_attr(queryset, attr):
    return sum(getattr(obj, attr, 0) for obj in queryset)