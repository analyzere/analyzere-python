import copy
from datetime import datetime
import json

import pytest
import mock
from six import StringIO

import analyzere
from analyzere import MissingIdError
from analyzere.resources import Layer
from analyzere.base_resources import (
    AnalyzeReObject,
    DataResource,
    EmbeddedResource,
    MetricsResource,
    OptimizationResource,
    Reference,
    Resource,
    convert_to_analyzere_object
)
from analyzere.errors import RetryAfter


class SetBaseUrl(object):
    def setup_method(self, _):
        analyzere.base_url = 'https://api'

    def teardown_method(self, _):
        analyzere.base_url = ''


class SequentialStreamWrapper(object):
    """
    Helper class to turn any file-like object into a stream from which can only
    be sequentially read. That is, this object does not support ``seek`` and
    ``tell`` operations for random access and stream positioning.
    """
    def __init__(self, file_obj):
        self.file_obj = file_obj

    def read(self, size=None):
        if size is None:
            return self.file_obj.read()
        else:
            return self.file_obj.read(size)


class TestReferences(SetBaseUrl):
    def test_known_resource(self, reqmock):
        reqmock.get('https://api/layers/abc123', status_code=200,
                    text='{"id": "abc123", "foo": "bar"}')
        href = 'https://api/layers/abc123'
        r = Reference(href)

        # Test laziness
        assert r._id == 'abc123'
        assert reqmock.call_count == 0

        # Force evaluation
        assert r.id == 'abc123'
        assert r.foo == 'bar'
        assert reqmock.call_count == 1
        assert isinstance(r, Layer)

    def test_unknown_resource(self, reqmock):
        reqmock.get('https://api/foo/abc123', status_code=200,
                    text='{"id": "abc123", "foo": "bar"}')
        href = 'https://api/foo/abc123'
        r = Reference(href)
        assert r._id == 'abc123'
        assert r.foo == 'bar'
        assert isinstance(r, Resource)

    def test_copy_unresolved(self, reqmock):
        reqmock.get('https://api/foos/abc123', status_code=200,
                    text='{"id": "abc123"}')
        a = Reference('https://api/foos/abc123')
        b = copy.copy(a)
        assert b._id == 'abc123'
        assert reqmock.call_count == 0

    def test_copy_resolved(self, reqmock):
        reqmock.get('https://api/foos/abc123', status_code=200,
                    text='{"id": "abc123", "list": [1, 2, 3]}')
        a = Reference('https://api/foos/abc123')
        assert a.list == [1, 2, 3]  # Forces evaluation
        b = copy.copy(a)
        assert b.list is a.list  # Assert copy was shallow
        assert reqmock.call_count == 1

    def test_deepcopy_unresolved(self, reqmock):
        reqmock.get('https://api/foos/abc123', status_code=200,
                    text='{"id": "abc123"}')
        a = Reference('https://api/foos/abc123')
        b = copy.deepcopy(a)
        assert b._id == 'abc123'
        assert reqmock.call_count == 0

    def test_deepcopy_resolved(self, reqmock):
        reqmock.get('https://api/foos/abc123', status_code=200,
                    text='{"id": "abc123", "list": [1, 2, 3]}')
        a = Reference('https://api/foos/abc123')
        assert a.list == [1, 2, 3]  # Forces evaluation
        b = copy.deepcopy(a)
        assert b.id == 'abc123'
        assert b.list is not a.list  # Assert copy was not shallow
        assert reqmock.call_count == 1


class TestAnalyzeReObject:
    def test_initialize_from_kwargs(self):
        a = AnalyzeReObject(foo='bar', baz='qux')
        assert a.foo == 'bar'
        assert a.baz == 'qux'

    def test_update(self):
        a = AnalyzeReObject(foo='bar', baz='qux')
        b = AnalyzeReObject(foo='fizz')
        a.update(b)
        assert a.foo == 'fizz'
        assert a.baz == 'qux'

    def test_clear(self):
        a = AnalyzeReObject(foo='bar', baz='qux')
        a.clear()
        assert not hasattr(a, 'foo')
        assert not hasattr(a, 'baz')

    def test_str(self):
        a = AnalyzeReObject(foo='bar', baz='qux')
        assert str(a) == '{\n  "baz": "qux",\n  "foo": "bar"\n}'

    def test_repr(self):
        a = AnalyzeReObject(foo='bar', baz='qux')
        assert (repr(a) == '<AnalyzeReObject at %s> JSON: {\n  '
                           '"baz": "qux",\n  "foo": "bar"\n}' % hex(id(a)))


class TestAnalyzeReObjectToDict:
    def test_simple(self):
        d = datetime.today()
        s = AnalyzeReObject(
            num=1,
            str='foo',
            date=d,
            list=[1, 2, 3],
            dict={'foo': 'bar'},
            ref=Reference('https://api/layers/abc123'),
            res=Resource(id='abc123', foo='bar')
        ).to_dict()

        assert s == {
            'num': 1,
            'str': 'foo',
            'date': d,
            'list': [1, 2, 3],
            'dict': {'foo': 'bar'},
            'ref': {'ref_id': 'abc123'},
            'res': {'ref_id': 'abc123'}
        }

    def test_nested(self):
        d = datetime.today()
        num = AnalyzeReObject(num=1)
        str_ = AnalyzeReObject(str='foo')
        date = AnalyzeReObject(date=d)
        list_ = AnalyzeReObject(list=[1, 2, 3])
        dict_ = AnalyzeReObject(dict={'foo': 'bar'})
        ref = AnalyzeReObject(ref=Reference('https://api/layers/abc123'))
        res = AnalyzeReObject(res=Resource(id='abc123', foo='bar'))
        s = AnalyzeReObject(num=num, str=str_, date=date, list=list_,
                            dict=dict_, ref=ref, res=res).to_dict()
        assert s == {
            'num': {'num': 1},
            'str': {'str': 'foo'},
            'date': {'date': d},
            'list': {'list': [1, 2, 3]},
            'dict': {'dict': {'foo': 'bar'}},
            'ref': {'ref': {'ref_id': 'abc123'}},
            'res': {'res': {'ref_id': 'abc123'}}
        }

    def test_id_not_stripped(self):
        s = AnalyzeReObject(id='abc123').to_dict()
        assert 'id' in s

    def test_private_stripped(self):
        s = AnalyzeReObject(_foo='bar').to_dict()
        assert '_foo' not in s

    def test_type_renamed(self):
        s = AnalyzeReObject(type='bar').to_dict()
        assert 'type' not in s
        assert s['_type'] == 'bar'

    def test_resources_without_id_inlined(self):
        s = AnalyzeReObject(res=Resource(foo='bar')).to_dict()
        assert 'foo' in s['res']
        assert s['res']['foo'] == 'bar'
        assert 'ref_id' not in s['res']


class TestConvertToAnalyzeReObject:
    def test_simple(self):
        d = datetime.today()
        resp = {
            'num': 1,
            'str': 'foo',
            'date': d,
            'list': [1, 2, 3],
            'dict': {'foo': 'bar'},
            'ref': {'href': 'https://api/layers/abc123'},
        }

        o = convert_to_analyzere_object(resp)
        assert o.num == 1
        assert o.str == 'foo'
        assert o.date == d
        assert o.list == [1, 2, 3]
        assert o.dict == EmbeddedResource(foo='bar')
        assert type(o.dict) == EmbeddedResource

        # Shallow comparison for reference so it doesn't evaluate
        assert type(o.ref) == Reference
        assert o.ref._id == 'abc123'

    def test_nested(self):
        d = datetime.today()
        resp = {
            'num': {'num': 1},
            'str': {'str': 'foo'},
            'date': {'date': d},
            'list': {'list': [1, 2, 3]},
            'dict': {'dict': {'foo': 'bar'}},
            'ref': {'ref': {'href': 'https://api/layers/abc123'}}
        }
        o = convert_to_analyzere_object(resp)
        assert o.num.num == 1
        assert o.str.str == 'foo'
        assert o.date.date == d
        assert o.list.list == [1, 2, 3]
        assert o.dict.dict == EmbeddedResource(foo='bar')
        assert type(o.ref.ref) == Reference
        assert o.ref.ref._id == 'abc123'

    def test_object_type(self):
        o = convert_to_analyzere_object({'id': 'abc123'})
        assert type(o) == EmbeddedResource

        o = convert_to_analyzere_object({'id': 'abc123'}, cls=Resource)
        assert type(o) == Resource

        o = convert_to_analyzere_object({'foo': 'bar'}, cls=Resource)
        assert type(o) == EmbeddedResource

        resp = {'id': 'abc123', 'embedded': {'foo': 'bar'}}
        o = convert_to_analyzere_object(resp, cls=Resource)
        assert type(o.embedded) == EmbeddedResource

        resp = {'id': 'abc123', 'embedded': {'id': 'xyz456', 'foo': 'bar'}}
        o = convert_to_analyzere_object(resp, cls=Resource)
        assert type(o) == Resource
        assert type(o.embedded) == EmbeddedResource

    def test_private_not_stripped(self):
        # TODO: Maybe underscore prefixed attributes from the server
        # (besides _type) should be ignored?
        o = convert_to_analyzere_object({'_private': 'foo'})
        assert o._private == 'foo'

    def test_type_renamed(self):
        resp = {'_type': {'foo'}}
        o = convert_to_analyzere_object(resp)
        assert not hasattr(o, '_type')
        assert hasattr(o, 'type')

    def test_collection(self):
        resp = {
            'items': [{'id': 'abc123'}, {'id': 'xyz456'}],
            'meta': {
                'limit': 0,
                'offset': 0,
                'total_count': 2,
                'future_attr': 'foo'
            }
        }
        o = convert_to_analyzere_object(resp, Resource)
        assert len(o) == 2
        assert o.meta.limit == 0
        assert o.meta.offset == 0
        assert o.meta.total_count == 2
        assert o.meta.future_attr == 'foo'
        assert type(o[0]) == Resource

        # TODO: When no class is provided, the items should probably be
        # AnalyzeReObjects
        o = convert_to_analyzere_object(resp)
        assert type(o[0]) == EmbeddedResource


class Foo(Resource):
    pass


class TestResource(SetBaseUrl):
    def test_retrieve(self, reqmock):
        reqmock.get('https://api/foos/abc123', status_code=200,
                    text='{"id": "abc123"}')
        f = Foo.retrieve('abc123')
        assert f == Foo(id='abc123')

    def test_list(self, reqmock):
        body = json.dumps({
            'items': [{'id': 'abc123'}, {'id': 'xyz456'}],
            'meta': {
                'limit': 0,
                'offset': 0,
                'total_count': 2,
            }
        })
        reqmock.get('https://api/foos/', status_code=200, text=body)
        f = Foo.list()
        assert len(f) == 2

        # With query params
        Foo.list(foo='bar')
        assert reqmock.last_request.query == 'foo=bar'

    def test_save_new(self, reqmock):
        reqmock.post('https://api/foos/', status_code=200,
                     text='{"id": "abc123", "server_generated": "foo"}')
        f = Foo(foo='bar')

        assert not hasattr(f, 'server_generated')
        f.save()
        assert reqmock.call_count == 1
        assert not hasattr(f, 'foo')
        assert f.server_generated == 'foo'

    def test_update(self, reqmock):
        reqmock.put('https://api/foos/abc123', status_code=200,
                    text='{"id": "abc123", "server_generated": "foo"}')
        f = Foo(id='abc123', foo='bar')
        f.save()
        assert reqmock.call_count == 1
        assert f.server_generated == 'foo'

    def test_reload(self, reqmock):
        reqmock.get('https://api/foos/abc123', status_code=200,
                    text='{"id": "abc123", "foo": "baz"}')

        f = Foo(foo='bar', throwaway='gone')
        with pytest.raises(MissingIdError):
            f.reload()

        f.id = 'abc123'
        f.reload()
        assert f.foo == 'baz'
        assert not hasattr(f, 'throwaway')


class Bar(DataResource):
    pass


class TestDataResource(SetBaseUrl):

    def test_download(self, reqmock):
        reqmock.get('https://api/bars/abc123/data', status_code=200,
                    text='data')
        f = Bar(id='abc123')
        assert f.download_data() == b'data'

    def test_upload_data(self, mock_bar_request):
        reqmock = mock_bar_request

        f = Bar(id='abc123')
        f.upload_data('data')
        assert reqmock.call_count == 4

        # Assert initiates session
        req = reqmock.request_history[0]
        assert req.headers['Entity-Length'] == '4'
        assert req.text is None

        # Assert uploads first chunk
        req = reqmock.request_history[1]
        assert req.headers['Content-Type'] == 'application/offset+octet-stream'
        assert req.headers['Content-Length'] == '4'
        assert req.headers['Offset'] == '0'
        assert req.text == 'data'

        # Assert session committed
        req = reqmock.request_history[2]
        assert req.text is None

        # Assert upload status checked
        req = reqmock.request_history[3]
        assert req.text is None

    def test_upload_data_file(self, mock_bar_request):
        reqmock = mock_bar_request

        f = Bar(id='abc123')

        # Create file object
        file_obj = StringIO('data')

        f.upload_data(file_obj)
        assert reqmock.call_count == 4

        # Assert initiates session
        req = reqmock.request_history[0]
        assert req.headers['Entity-Length'] == '4'
        assert req.text is None

        # Assert uploads first chunk
        req = reqmock.request_history[1]
        assert req.headers['Content-Type'] == 'application/offset+octet-stream'
        assert req.headers['Content-Length'] == '4'
        assert req.headers['Offset'] == '0'
        assert req.text == 'data'

        # Assert session committed
        req = reqmock.request_history[2]
        assert req.text is None

        # Assert upload status checked
        req = reqmock.request_history[3]
        assert req.text is None

    def test_upload_data_stream(self, mock_bar_request):
        reqmock = mock_bar_request

        f = Bar(id='abc123')

        # Create file object
        file_obj = SequentialStreamWrapper(StringIO('data'))

        f.upload_data(file_obj)
        assert reqmock.call_count == 4

        # Assert initiates session
        req = reqmock.request_history[0]
        assert 'Entity-Length' not in req.headers
        assert req.text is None

        # Assert uploads first chunk
        req = reqmock.request_history[1]
        assert req.headers['Content-Type'] == 'application/offset+octet-stream'
        assert req.headers['Content-Length'] == '4'
        assert req.headers['Offset'] == '0'
        assert req.text == 'data'

        # Assert session committed
        req = reqmock.request_history[2]
        assert req.text is None

        # Assert upload status checked
        req = reqmock.request_history[3]
        assert req.text is None

    def test_upload_data_chunking(self, mock_bar_request):
        reqmock = mock_bar_request

        f = Bar(id='abc123')

        # Create file object
        file_obj = StringIO('data')

        # Set chunking to 3 bytes per chunk
        # Upload file
        f.upload_data(file_obj, chunk_size=3)

        assert reqmock.call_count == 5

        # Assert initiates session
        req = reqmock.request_history[0]
        assert req.headers['Entity-Length'] == '4'
        assert req.text is None

        # Assert uploads first chunk
        req = reqmock.request_history[1]
        assert req.headers['Content-Type'] == 'application/offset+octet-stream'
        assert req.headers['Content-Length'] == '3'
        assert req.headers['Offset'] == '0'
        assert req.text == 'dat'

        # Assert uploads second chunk
        req = reqmock.request_history[2]
        assert req.headers['Content-Type'] == 'application/offset+octet-stream'
        assert req.headers['Content-Length'] == '1'
        assert req.headers['Offset'] == '3'
        assert req.text == 'a'

        # Assert session committed
        req = reqmock.request_history[3]
        assert req.text is None

        # Assert upload status checked
        req = reqmock.request_history[4]
        assert req.text is None

    def test_upload_data_chunking_bad_callbacks(self, mock_bar_request):
        f = Bar(id='abc123')

        # Create file object
        file_obj = StringIO('data')

        # call with bad callbacks
        with pytest.raises(Exception) as e:
            f.upload_data(file_obj, chunk_size=1,
                          upload_callback='callback')
        assert str(e.value) == 'provided upload_callback is not callable'

        with pytest.raises(Exception) as e:
            f.upload_data(file_obj, chunk_size=1,
                          commit_callback='callback')
        assert str(e.value) == 'provided commit_callback is not callable'

    def test_upload_data_chunking_callbacks(self, mock_bar_request):
        reqmock = mock_bar_request
        upload_callback = mock.Mock()
        commit_callback = mock.Mock()

        f = Bar(id='abc123')

        # Create file object of 10 bytes
        file_obj = StringIO('1234567890')

        # Set chunking to 1 byte per chunk == 10 chunks
        # Upload file
        f.upload_data(file_obj, chunk_size=1,
                      upload_callback=upload_callback,
                      commit_callback=commit_callback)

<<<<<<< HEAD
        assert reqmock.call_count == 13
        assert upload_callback.call_count == 11
        assert upload_callback.called_with(100.0)
        assert commit_callback.call_count == 1
        assert commit_callback.called_with(100.0)
=======
        assert reqmock.call_count == 7
        assert upload_callback.call_count == 6
        assert upload_callback == 100.0
        assert commit_callback_count == 1
        assert commit_callback_progress == 100.0
>>>>>>> code review

    def test_delete_data(self, reqmock):
        reqmock.delete('https://api/bars/abc123/data', status_code=201)
        Bar(id='abc123').delete_data()
        assert reqmock.call_count == 1


class FooView(MetricsResource):
    pass


class TestMetricsResource(SetBaseUrl):
    def test_tail_metrics(self, reqmock):
        reqmock.get('https://api/foo_views/abc123/tail_metrics/1.0',
                    status_code=200, text='{"num": 1.0}')
        f = FooView(id='abc123')
        assert f.tail_metrics(1.0).num == 1.0

        reqmock.get('https://api/foo_views/abc123/tail_metrics/0.5,1.0',
                    status_code=200, text='[{"num": 1.0}, {"num": 2.0}]')
        tm = f.tail_metrics([0.5, 1.0])
        assert len(tm) == 2
        assert tm[0].num == 1.0
        assert tm[1].num == 2.0

    def test_co_metrics(self, reqmock):
        reqmock.get('https://api/foo_views/abc123/co_metrics/1.0',
                    status_code=200, text='{"num": 1.0}')
        f = FooView(id='abc123')
        assert f.co_metrics(1.0).num == 1.0

        reqmock.get('https://api/foo_views/abc123/co_metrics/0.5,1.0',
                    status_code=200, text='[{"num": 1.0}, {"num": 2.0}]')
        tm = f.co_metrics([0.5, 1.0])
        assert len(tm) == 2
        assert tm[0].num == 1.0
        assert tm[1].num == 2.0

    def test_el(self, reqmock):
        reqmock.get('https://api/foo_views/abc123/el', status_code=200,
                    text='1.0')
        f = FooView(id='abc123')
        assert f.el() == 1.0

    def test_ep(self, reqmock):
        reqmock.get('https://api/foo_views/abc123/exceedance_probabilities/1',
                    status_code=200, text='{"num": 1.0}')
        f = FooView(id='abc123')
        assert f.ep(1).num == 1.0

        reqmock.get('https://api/foo_views/abc123/exceedance_probabilities/'
                    '100,200', status_code=200,
                    text='[{"num": 1.0}, {"num": 2.0}]')
        tm = f.ep([100, 200])
        assert len(tm) == 2
        assert tm[0].num == 1.0
        assert tm[1].num == 2.0

    def test_ep_auto_retry_true(self, reqmock):
        responses = [
            {'status_code': 503, 'headers': {'Retry-After': '0.01'}},
            {'status_code': 200, 'text': '{"num": 1.0}'}
        ]
        reqmock.get('https://api/foo_views/abc123/exceedance_probabilities/1',
                    responses)
        f = FooView(id='abc123')
        with mock.patch('time.sleep') as sleep:
            assert f.ep(1, auto_retry=True).num == 1.0
        sleep.assert_called_once_with(0.01)

    def test_ep_auto_retry_false(self, reqmock):
        responses = [
            {'status_code': 503, 'headers': {'Retry-After': '0.01'}},
            {'status_code': 200, 'text': '{"num": 1.0}'}
        ]
        reqmock.get('https://api/foo_views/abc123/exceedance_probabilities/1',
                    responses)
        f = FooView(id='abc123')
        with pytest.raises(RetryAfter):
            f.ep(1, auto_retry=False).num
        assert f.ep(1, auto_retry=False).num == 1.0

    def test_tvar(self, reqmock):
        reqmock.get('https://api/foo_views/abc123/tvar/1.0', status_code=200,
                    text='1.0')
        f = FooView(id='abc123')
        assert f.tvar(1.0) == 1.0

        reqmock.get('https://api/foo_views/abc123/tvar/0.5,1.0',
                    status_code=200, text='[{"num": 1.0}, {"num": 2.0}]')
        tm = f.tvar([0.5, 1.0])
        assert len(tm) == 2
        assert tm[0].num == 1.0
        assert tm[1].num == 2.0

    def test_download_ylt(self, reqmock):
        reqmock.get('https://api/foo_views/abc123/ylt', status_code=200,
                    text='ylt-data')
        f = FooView(id='abc123')
        assert f.download_ylt() == b'ylt-data'

    def test_download_yelt(self, reqmock):
        reqmock.get('https://api/foo_views/abc123/yelt', status_code=200,
                    text='yelt-data')
        f = FooView(id='abc123')
        assert f.download_yelt() == b'yelt-data'

    def test_download_yelt_auto_retry_true(self, reqmock):
        responses = [
            {'status_code': 503, 'headers': {'Retry-After': '0.01'}},
            {'status_code': 200, 'text': 'yelt-data'}
        ]
        reqmock.get('https://api/foo_views/abc123/yelt', responses)
        f = FooView(id='abc123')
        with mock.patch('time.sleep') as sleep:
            assert f.download_yelt() == b'yelt-data'
        sleep.assert_called_once_with(0.01)

    def test_download_yelt_auto_retry_false(self, reqmock):
        responses = [
            {'status_code': 503, 'headers': {'Retry-After': '0.01'}},
            {'status_code': 200, 'text': 'yelt-data'}
        ]
        reqmock.get('https://api/foo_views/abc123/yelt', responses)
        f = FooView(id='abc123')
        with pytest.raises(RetryAfter):
            f.download_yelt(auto_retry=False)
        assert f.download_yelt(auto_retry=False) == b'yelt-data'

    def test_unknown_resource_equality(self, reqmock):
        reqmock.get('https://api/foo/abc123', status_code=200,
                    text='{"id": "abc123", "foo": "bar"}')
        href = 'https://api/foo/abc123'
        r1 = Reference(href)
        r2 = Reference(href)
        assert r1 == r2

    def test_back_allocation(self, reqmock):
        reqmock.get(
            'https://api/foo_views/abc123/back_allocations?source_id=321cba',
            status_code=200,
            text='"response_object"'
        )
        f = FooView(id='abc123')
        response = f.back_allocation("321cba")
        assert response == "response_object"

    # TODO: Add tests for id: None


class BazView(OptimizationResource):
    pass


class TestOptimizationResource(SetBaseUrl):
    def test_get_results(self, reqmock):
        reqmock.get('https://api/baz_views/abc123/result', status_code=200,
                    text='{"num": 1.0}')
        f = BazView(id='abc123')
        assert f.result().num == 1.0
