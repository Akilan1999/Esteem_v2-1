from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='path_contains')
def path_contains(request, token):
    return token in request.path

@register.filter(name='get_group_name')
def get_group_name(user, user1):
    return [x for x in user.groups.values_list('name', flat=True)]

