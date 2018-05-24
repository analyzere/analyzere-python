import json
from datetime import datetime, tzinfo, timedelta

import pytest
import six
from six import StringIO

from analyzere import utils
from analyzere.errors import InvalidProbabilityError


class TestStringHelpers:
    def test_to_snake_case(self):
        assert utils.to_snake_case('MyCamelCase') == 'my_camel_case'
        assert utils.to_snake_case('myCamelCase') == 'my_camel_case'
        assert utils.to_snake_case('Camel') == 'camel'

    def test_to_camel_case(self):
        assert utils.to_camel_case('my_camel_case') == 'MyCamelCase'
        assert utils.to_camel_case('camel') == 'Camel'


class TestDateTimeEncoder:
    def test_with_timezone(self):
        class GMT2(tzinfo):
            def utcoffset(self, dt):
                return timedelta(hours=2)

        d = {'d': datetime(2015, 6, 1, 12, tzinfo=GMT2())}
        js = json.dumps(d, cls=utils.DateTimeEncoder)
        assert js == '{"d": "2015-06-01T12:00:00+02:00"}'

    def test_without_timezone(self):
        d = {'d': datetime(2015, 6, 1, 12)}
        js = json.dumps(d, cls=utils.DateTimeEncoder)
        assert js == '{"d": "2015-06-01T12:00:00"}'


class TestDateTimeDecoder:
    def test_valid_date_with_ms(self):
        d = json.loads('{"d": "2015-06-01T12:00:00.123456Z"}',
                       cls=utils.DateTimeDecoder)
        assert d['d'] == datetime(2015, 6, 1, 12, 0, 0, 123456,
                                  tzinfo=utils.UTC())

    def test_valid_date_without_ms(self):
        d = json.loads('{"d": "2015-06-01T12:00:00Z"}',
                       cls=utils.DateTimeDecoder)
        assert d['d'] == datetime(2015, 6, 1, 12, 0, 0, tzinfo=utils.UTC())

    def test_with_invalid_date(self):
        d = json.loads('{"d": "06-01T12:00:00Z"}',
                       cls=utils.DateTimeDecoder)
        assert d['d'] == '06-01T12:00:00Z'

    def test_with_incompatible_date(self):
        d = json.loads('{"d": "2015-06-01T12:00:00+02:00"}',
                       cls=utils.DateTimeDecoder)
        assert d['d'] == '2015-06-01T12:00:00+02:00'


class TestReadInChunks:
    def test_valid_chunk_size(self):
        s = StringIO('foob')
        reader = utils.read_in_chunks(s, 2)
        assert six.next(reader) == ('fo', 0)
        assert six.next(reader) == ('ob', 2)
        with pytest.raises(StopIteration):
            six.next(reader)

    def test_large_chunk_size(self):
        s = StringIO('foob')
        reader = utils.read_in_chunks(s, 5)
        assert six.next(reader) == ('foob', 0)

    def test_small_chunk_size(self):
        s = StringIO('foob')
        reader = utils.read_in_chunks(s, 0)
        with pytest.raises(StopIteration):
            six.next(reader)


def test_file_length():
    s = StringIO('foobar')
    assert utils.file_length(s) == 6
    s.seek(3)
    assert utils.file_length(s) == 6


def test_vectorize():
    x = 123
    assert utils.vectorize(x) == 123
    x = [123, 456]
    assert utils.vectorize(x) == '123,456'


@pytest.mark.parametrize('values, returns', [
    ((1, 3), '1_3'),
    ([(1, 3), (2, 4)], '1_3,2_4'),
    ((1, '3'), '1_3'),
    ((1, 'str'), '1_str'),
    ((1, 2, 3), '1_2_3'),
    (123, '123'),
])
def test_vectorize_range(values, returns):
    assert utils.vectorize_range(values) == returns


def test_vectorize_range_invalid():
    x = [1, 2, 3]
    with pytest.raises(InvalidProbabilityError) as e:
        utils.vectorize_range(x)
    assert str(e.value) == 'Items in the list must be tuples'
