import pytest

import analyzere
from analyzere import MonetaryUnit, LayerPolicy
from analyzere.resources import PortfolioView, LayerView


class SetBaseUrl(object):
    def setup_method(self, _):
        analyzere.base_url = 'https://api'

    def teardown_method(self, _):
        analyzere.base_url = ''


class TestMonetaryUnit:
    def test_init_with_pos_arg(self):
        m = MonetaryUnit(123, 'USD')
        assert m.value == 123
        assert m.currency == 'USD'

        with pytest.raises(TypeError):
            MonetaryUnit(123)

    def test_init_with_kwargs(self):
        m = MonetaryUnit(123, currency='USD')
        assert m.value == 123
        assert m.currency == 'USD'

        m = MonetaryUnit(value=123, currency='USD')
        assert m.value == 123


class TestLayerPolicy:
    def test_init_with_pos_arg(self):
        policy = LayerPolicy(["Loss"], [])
        assert policy.transform_records == ["Loss"]
        assert policy.forward_records == []

        with pytest.raises(TypeError):
            LayerPolicy([])

    def test_init_with_kwargs(self):
        policy = LayerPolicy(["Loss"], forward_records=[])
        assert policy.transform_records == ["Loss"]
        assert policy.forward_records == []

        policy = LayerPolicy(transform_records=["Loss"], forward_records=[])
        assert policy.transform_records == ["Loss"]


class TestMarginal(SetBaseUrl):
    def test_get_results(self, reqmock):
        reqmock.post(
            'https://api/portfolio_view_marginals',
            status_code=200,
            text='{"portfolio_view": {"ref_id": "a1"}}')

        # The returned reference will be resolved, so we must mock both requests
        reqmock.get('https://api/portfolio_views/a1', status_code=200,
                    text='{"id": "a1"}')

        f = PortfolioView(id='abc123')
        lv_to_add = LayerView(id='xxx')
        lv_to_remove = LayerView(id='yyy')

        pv = f.marginal(
            [lv_to_add],
            [lv_to_remove],
        )

        assert reqmock.request_history[0].method == 'POST'

        req_json = reqmock.request_history[0].json()

        assert req_json['portfolio_view_id']['ref_id'] == 'abc123'
        assert len(req_json['add_layer_view_ids']) == 1
        assert len(req_json['remove_layer_view_ids']) == 1
        assert req_json['add_layer_view_ids'][0]['ref_id'] == 'xxx'
        assert req_json['remove_layer_view_ids'][0]['ref_id'] == 'yyy'

        assert pv.id == 'a1'
