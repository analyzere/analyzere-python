import copy
import json
import time

from lazy_object_proxy import Proxy
import six
import uuid
from six import StringIO

import analyzere
from analyzere import utils
from analyzere.errors import MissingIdError
from analyzere.requestor import request, request_raw
from analyzere.utils import vectorize


# Helpers

class PaginatedCollection(list):
    def __init__(self, items, meta):
        super(PaginatedCollection, self).__init__(items)
        self.meta = meta


class Reference(Proxy):
    _id = None
    _href = None
    _resolved = False

    def __init__(self, href):
        collection_name, self._id = utils.parse_href(href)
        self._href = href

        def resolve():
            r = load_reference(collection_name, self._id)
            self._resolved = True
            return r

        super(Reference, self).__init__(resolve)

    def __copy__(self):
        if self._resolved:
            return copy.copy(self.__wrapped__)
        return Reference(self._href)

    def __deepcopy__(self, memo):
        if self._resolved:
            return copy.deepcopy(self.__wrapped__, memo)
        return Reference(self._href)


def load_reference(collection_name, id_):
    class_name = utils.to_camel_case(collection_name[:-1])
    try:
        cls = getattr(analyzere, class_name)
    except AttributeError:
        # For references to resources we don't know about, create a Resource
        # subclass with the correct collection name so retrieve() works.
        class UnknownResource(Resource):
            _collection_name = collection_name

            def __eq__(self, other):
                # Overridden since the super would compare that other is an
                # instance of self.__class__ but each UnknownResource has it's
                # own class. An alternative would be to store a map (dict) from
                # collection name -> UnknownResource classes, and ensure only
                # one is made for each collection.
                return self.__dict__ == other.__dict__
        cls = UnknownResource
    return cls.retrieve(id_)


def convert_to_analyzere_object(value, cls=None):
    if isinstance(value, list):
        return [convert_to_analyzere_object(v, cls) for v in value]
    elif isinstance(value, dict):
        if 'href' in value:
            return Reference(value['href'])

        if 'items' in value and 'meta' in value:
            items = convert_to_analyzere_object(value['items'], cls)
            meta = convert_to_analyzere_object(value['meta'])
            return PaginatedCollection(items, meta)

        obj = cls() if (cls and 'id' in value) else EmbeddedResource()
        for k, v in six.iteritems(value):
            # Rename "_type" attribute to "type" so it's not considered private
            if k == '_type':
                k = 'type'
            setattr(obj, k, convert_to_analyzere_object(v))
        return obj
    else:
        return value


def to_dict(value):
    if isinstance(value, Reference):
        # Should appear first since other isinstance() checks may evaluate
        # the reference.
        return {'ref_id': value._id}
    elif isinstance(value, Resource):
        # Resources with IDs should be referenced, otherwise they're inlined
        if hasattr(value, 'id'):
            return {'ref_id': value.id}
        else:
            return value.to_dict()
    elif hasattr(value, 'to_dict'):
        return value.to_dict()
    elif isinstance(value, list):
        return [to_dict(i) for i in value]
    else:
        return value


# Base classes

class AnalyzeReObject(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return json.dumps(self.to_dict(), sort_keys=True, indent=2,
                          separators=(',', ': '), cls=utils.DateTimeEncoder)

    def __repr__(self):
        ident_parts = [type(self).__name__]

        id_ = getattr(self, 'id', None)
        if id_:
            ident_parts.append('id=%s' % id_)

        repr_str = '<%s at %s> JSON: %s' % (
            ' '.join(ident_parts), hex(id(self)), str(self))

        return repr_str

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def update(self, other):
        return self.__dict__.update(other.__dict__)

    def clear(self):
        return self.__dict__.clear()

    def to_dict(self):
        d = {}
        for k, v in six.iteritems(self.__dict__):
            if isinstance(k, str) and k.startswith('_'):
                continue
            elif k == 'type':
                k = '_type'
            d[k] = to_dict(v)
        return d

    def __hash__(self):
        # Certainly not the most efficient hash, since anything without an ID
        # has the same hash value.
        if hasattr(self, 'id'):
            int(uuid.UUID(self.id))
        return 0


class Resource(AnalyzeReObject):
    """
    Base class for all API resources. Note that when a resource is saved,
    all values set on the object will be erased and replaced with the values
    returned from the server. This may result in attributes you have set that
    are ignored by the server being cleared.
    """
    _collection_name = None

    @classmethod
    def _get_collection_name(cls):
        if cls._collection_name:
            return cls._collection_name
        else:
            return utils.to_snake_case(cls.__name__) + 's'

    @classmethod
    def _get_path(cls, id_=None):
        path = cls._get_collection_name() + '/'
        return path + id_ if id_ else path

    @classmethod
    def retrieve(cls, id_):
        resp = request('get', cls._get_path(id_))
        return convert_to_analyzere_object(resp, cls)

    @classmethod
    def list(cls, **params):
        resp = request('get', cls._get_path(), params=params)
        return convert_to_analyzere_object(resp, cls)

    def save(self):
        id_ = getattr(self, 'id', None)
        method = 'put' if id_ else 'post'
        resp = request(method, self._get_path(id_), data=self.to_dict())
        self.clear()
        self.update(convert_to_analyzere_object(resp))
        return self

    def reload(self):
        id_ = getattr(self, 'id', None)
        if not id_:
            raise MissingIdError()
        self.clear()
        self.update(self.retrieve(id_))
        return self


class EmbeddedResource(AnalyzeReObject):
    pass


class DataResource(Resource):
    @property
    def _data_path(self):
        return self._get_path(self.id) + '/data'

    @property
    def _status_path(self):
        return self._data_path + '/status'

    @property
    def _commit_path(self):
        return self._data_path + '/commit'

    @property
    def upload_status(self):
        resp = request('get', self._status_path)
        return convert_to_analyzere_object(resp)

    def upload_data(self, file_or_str):
        """
        Accepts a file-like object or string and uploads it. Files are
        automatically uploaded in 4mb chunks. Implements the tus protocol.
        """
        file_obj = StringIO(file_or_str) if isinstance(
            file_or_str, six.string_types) else file_or_str
        chunk_size = 4 * 1024 * 1024
        length = utils.file_length(file_obj)

        # Initiate upload session
        request_raw('post', self._data_path, headers={
            'Entity-Length': str(length)
        })

        # Upload chunks
        for chunk, offset in utils.read_in_chunks(file_obj, chunk_size):
            headers = {'Offset': str(offset),
                       'Content-Type': 'application/offset+octet-stream'}
            request_raw('patch', self._data_path, headers=headers, body=chunk)

        # Commit the session
        request_raw('post', self._commit_path)

        # Block until data has finished processing
        while True:
            resp = self.upload_status
            if (resp.status == 'Processing Successful' or
                    resp.status == 'Processing Failed'):
                return resp
            else:
                time.sleep(analyzere.upload_poll_interval)

    def download_data(self):
        return request_raw('get', self._data_path).content

    def delete_data(self):
        request_raw('delete', self._data_path)


class MetricsResource(Resource):
    """
    TODO: should the names of these functions be improved?
    """
    def _get_metrics(self, path, params=None, auto_retry=True):
        resp = request('get', path, params=params, auto_retry=auto_retry)
        return convert_to_analyzere_object(resp)

    def tail_metrics(self, probabilities, auto_retry=True, **params):
        probabilities = vectorize(probabilities)
        path = '%s/tail_metrics/%s' % (self._get_path(self.id), probabilities)
        return self._get_metrics(path, params, auto_retry=auto_retry)

    def co_metrics(self, probabilities, auto_retry=True, **params):
        probabilities = vectorize(probabilities)
        path = '%s/co_metrics/%s' % (self._get_path(self.id), probabilities)
        return self._get_metrics(path, params, auto_retry=auto_retry)

    def el(self, auto_retry=True, **params):
        path = '%s/el' % self._get_path(self.id)
        return float(
            request('get', path, params=params, auto_retry=auto_retry))

    def ep(self, thresholds, auto_retry=True, **params):
        thresholds = vectorize(thresholds)
        path = '%s/exceedance_probabilities/%s' % (self._get_path(self.id),
                                                   thresholds)
        return self._get_metrics(path, params, auto_retry=auto_retry)

    def tvar(self, probabilities, auto_retry=True, **params):
        probabilities = vectorize(probabilities)
        path = '%s/tvar/%s' % (self._get_path(self.id), probabilities)
        resp = self._get_metrics(path, params, auto_retry=auto_retry)
        return resp if isinstance(resp, list) else float(resp)

    def download_ylt(self, auto_retry=True, **params):
        path = '%s/ylt' % self._get_path(self.id)
        return request_raw(
            'get', path, params=params, auto_retry=auto_retry).content

    def download_yelt(self, auto_retry=True, **params):
        path = '%s/yelt' % self._get_path(self.id)
        return request_raw(
            'get', path, params=params, auto_retry=auto_retry).content

    def back_allocation(self, source_id, auto_retry=True, **params):
        params['source_id'] = source_id
        path = '%s/back_allocations' % self._get_path(self.id)
        data = request('get', path, auto_retry=auto_retry, params=params)
        return convert_to_analyzere_object(data)


class OptimizationResource(Resource):
    def result(self):
        path = '%s/result' % self._get_path(self.id)
        resp = request('get', path)
        return convert_to_analyzere_object(resp)
