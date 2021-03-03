import json

from django import template
from django.template.defaultfilters import escapejs
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def to_js(value):
    encoded = escapejs(json.dumps(value))
    return mark_safe(f'JSON.parse("{encoded}")')
