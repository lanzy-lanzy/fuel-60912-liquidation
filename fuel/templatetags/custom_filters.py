from django import template

register = template.Library()

@register.filter
def sum_attr(queryset, attr):
    return sum(getattr(item, attr) for item in queryset)

@register.filter
def div(value, arg):
    try:
        return (value / arg) * 100  # Assuming you want a percentage
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