from django import template

register = template.Library()

@register.filter
def can_edit(user):
    return user.is_staff or user.is_superuser 