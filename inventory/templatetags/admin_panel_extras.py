from django import template


register = template.Library()


@register.filter
def getattr_value(obj, attr):
    return getattr(obj, attr, '')
