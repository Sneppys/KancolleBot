"""Handles the bot settings."""
import json
import os
import random

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(DIR_PATH, "../settings.json"), 'r') as sf:
    setting_data = json.load(sf)


def setting(path):
    """Return a setting in the settings file.

    Parameters
    ----------
    path : str
        Dot-separated location for the setting. e.g. ['foo']['bar'] being
        "foo.bar"
    """
    data = setting_data
    split = path.split('.')
    for c in split:
        data = data[c]
    return data


def namesub(string):
    """Substitute a string with settings.

    e.g. %xyz% to the setting 'names.xyz'
    %xyz.caps% goes to 'names.xyz' but in all uppercase
    %xyz.title% in title case
    """
    to_sub = setting('names')
    for k, v in to_sub.items():
        string = string.replace('%{0}.caps%'.format(k), v.upper())
        string = string.replace('%{0}.title%'.format(k), v.title())
        string = string.replace('%{0}%'.format(k), v)
    return string


def setting_random(string):
    """Get a random number in a setting's range."""
    range = setting(string)
    return range[0] + random.randrange(range[1] - range[0] + 1)
