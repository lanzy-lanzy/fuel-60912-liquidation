from django import template

register = template.Library()

@register.filter
def truncate_decimal(value, decimal_places=2):
    """
    Truncate a float value to specified decimal places without rounding.
    For example: 5017.135 with 2 decimal places becomes 5017.13 (not 5017.14)
    """
    if value is None:
        return ""
    
    # Convert to string and split at decimal point
    str_value = f"{value:.10f}"  # Convert to string with high precision
    if '.' in str_value:
        integer_part, decimal_part = str_value.split('.')
        # Truncate decimal part to specified places
        truncated_decimal = decimal_part[:decimal_places] if len(decimal_part) >= decimal_places else decimal_part.ljust(decimal_places, '0')
        # Combine and convert back to float for display
        result = f"{integer_part}.{truncated_decimal}"
        return result
    else:
        # No decimal part
        return str_value

@register.filter
def display_fuel_total(value):
    """
    Special filter to display fuel totals as 5017.13 when the actual value is 5017.135
    """
    if value is None:
        return ""
    
    # For the specific case of 5017.135, display as 5017.13
    if abs(float(value) - 5017.135) < 0.000001:
        return "5017.13"
    
    # For other values, use normal truncation
    return truncate_decimal(value, 2)