from django import template
register = template.Library()


@register.filter
def get_attr(obj, val):
    """Allows to check if user is doctor or patient inside HTML templates."""
    return getattr(obj, val, False)


