from django import template

register = template.Library()

@register.filter
def get_dict_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using the key.
    Usage: {{ dictionary|get_dict_item:key }}
    """
    return dictionary.get(key, '')