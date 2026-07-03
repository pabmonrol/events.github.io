from typing import NamedTuple
from datetime import date, time

Event = NamedTuple('Event', [('community', str),
                            ('title', str),
                            ('icon', str),
                            ('colour', str),
                            ('category', str),
                            ('date', date),
                            ('time', time),
                            ('location', str),
                            ('google_maps', str),
                            ('description', int),
                            ('price', float)])