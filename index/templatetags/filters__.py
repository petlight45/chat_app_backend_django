import os
from django import template

register = template.Library()

@register.filter
def get_tag(msg_type):
    if msg_type == 'error':
        return 'danger'
    elif msg_type == 'success':
        return 'success'
    elif msg_type == 'warning':
        return 'warning'
    return 'primary'