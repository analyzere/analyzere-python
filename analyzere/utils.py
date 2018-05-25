from datetime import datetime, timedelta, tzinfo
import json
import re

import six
from six.moves.urllib.parse import urlparse


class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class DateTimeDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = self.dict_to_object
        super(DateTimeDecoder, self).__init__(*args, **kwargs)

    def dict_to_object(self, d):
        for k, v in six.iteritems(d):
            # Dates from Analyze Re API currently come back in one of these two
            # formats. TODO: Loosen this restriction to be more forward
            # compatible.
            formats = ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ']
            parsed = parse_datetime(v, formats)
            if parsed:
                d[k] = parsed
        return d


def parse_datetime(value, formats):
    for f in formats:
        try:
            d = datetime.strptime(value, f)
            return d.replace(tzinfo=UTC())
        except (ValueError, TypeError):
            pass


def to_snake_case(camel_str):
    return re.sub('(?!^)([A-Z]+)', r'_\1', camel_str).lower()


def to_camel_case(snake_str):
    return ''.join([s.title() for s in snake_str.split('_')])


def file_length(file_obj):
    """
    Returns the length in bytes of a given file object.
    Necessary because os.fstat only works on real files and not file-like
    objects. This works on more types of streams, primarily StringIO.
    """
    file_obj.seek(0, 2)
    length = file_obj.tell()
    file_obj.seek(0)
    return length


def read_in_chunks(file_obj, chunk_size):
    """Generator to read a file piece by piece."""
    offset = 0
    while True:
        data = file_obj.read(chunk_size)
        if not data:
            break
        yield data, offset
        offset += len(data)


def parse_href(href):
    """Parses an Analyze Re href into collection name and ID"""
    url = urlparse(href)
    path = url.path.split('/')
    collection_name = path[1]
    id_ = path[2]
    return collection_name, id_


def vectorize(values):
    """
    Takes a value or list of values and returns a single result, joined by ","
    if necessary.
    """
    if isinstance(values, list):
        return ','.join(str(v) for v in values)
    return values


def vectorize_range(values):
    """
    This function is for url encoding.
    Takes a value or a tuple or list of tuples and returns a single result,
    tuples are joined by "," if necessary, elements in tuple are joined by '_'
    """
    if isinstance(values, tuple):
        return '_'.join(str(i) for i in values)
    if isinstance(values, list):
        if not all([isinstance(item, tuple) for item in values]):
            raise TypeError('Items in the list must be tuples')
        return ','.join('_'.join(str(i) for i in v) for v in values)
    return str(values)
