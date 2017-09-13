from __future__ import print_function

from random import SystemRandom
from .words import wordlist
from blessings import Terminal
term = Terminal()

SENTINEL = object()

sys_random = SystemRandom()

def _get_input(prompt, input_type=SENTINEL, default=SENTINEL):
    if input_type != SENTINEL and not isinstance(input_type, type):
        raise ValueError('Input type must be of type "type"')
    if (input_type != SENTINEL and
            default != SENTINEL and
            not isinstance(default, input_type)):
        raise ValueError('Type of default does not match input type')

    if default == SENTINEL:
        default = ''

    if input_type == SENTINEL:
        input_type = lambda x: x

    return input_type(raw_input(prompt) or default)

def _print(*args, **kwargs):
    formatters = kwargs.pop('formatters', None)
    if formatters:
        if isinstance(formatters, list):
            for formatter in formatters:
                print(formatter, end='')
        else:
            print(formatters, end='')

    print(*args, **kwargs)
    print(term.normal, end='')

def word_generator():
    while True:
        yield sys_random.choice(wordlist)
