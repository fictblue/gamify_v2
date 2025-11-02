from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the value by the arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get an item from a dictionary using a key."""
    if dictionary is None:
        return None
    return dictionary.get(key)
