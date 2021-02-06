from django.template.defaulttags import register


@register.filter(name='lookup')
def lookup(value, arg):
    return value.get(arg)

@register.filter(name='index')
def index(indexable, i):
    return indexable[i]

@register.filter(name='indexone')
def indexone(indexable, i):
    return indexable[i-1]