from django import template

register = template.Library()

@register.filter
def get_dict_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using its key
    Usage: {{ dictionary|get_dict_item:key }}
    """
    if dictionary is None:
        return None
    
    if not hasattr(dictionary, 'get'):
        return None
        
    return dictionary.get(key)