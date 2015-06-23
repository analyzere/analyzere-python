import pytest
import requests_mock


@pytest.fixture
def reqmock(request):
    m = requests_mock.Mocker()
    m.start()
    request.addfinalizer(lambda: m.stop())
    return m
