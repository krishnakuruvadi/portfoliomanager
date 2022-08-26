from django.template.defaulttags import register
from common.helper import get_current_app_version


@register.filter(name='lookup')
def lookup(value, arg):
    return value.get(arg)

@register.filter(name='index')
def index(indexable, i):
    return indexable[i]

@register.filter(name='indexone')
def indexone(indexable, i):
    return indexable[i-1]

@register.filter(name='getinternals')
def getinternals(comp, ignore):
    release_version = get_current_app_version()
    return release_version

