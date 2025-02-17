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
        return (float(value) / float(arg)) * 100  # Assuming you want a percentage
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