import pytest
import requests_mock


@pytest.fixture
def reqmock(request):
    m = requests_mock.Mocker()
    m.start()
    request.addfinalizer(lambda: m.stop())
    return m


@pytest.fixture
def mock_bar_request(reqmock):
    reqmock.post('https://api/bars/abc123/data', status_code=201,
                 text='data')
    reqmock.patch('https://api/bars/abc123/data', status_code=204)
    reqmock.post('https://api/bars/abc123/data/commit', status_code=204)
    reqmock.get('https://api/bars/abc123/data/status', status_code=200,
                text='{"status": "Processing Successful"}')
    return reqmock
