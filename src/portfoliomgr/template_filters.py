from django.template.defaulttags import register
import json
import os


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
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metadata_file = os.path.join(base_dir, 'metadata.json')
    metadata_file_exist = os.path.exists(metadata_file)

    if metadata_file_exist:
        with open(metadata_file) as file:
            metadata = json.load(file)
            try:
                release_version = metadata['release_version']
                return release_version

            except KeyError:
                release_version = 'Unable to retrieve'
                return release_version

    else:
        release_version = '0.0.1'
        return release_version
