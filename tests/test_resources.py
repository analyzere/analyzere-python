import pytest

import analyzere
from analyzere import MonetaryUnit, LayerPolicy
from analyzere.resources import PortfolioView, LayerView, ExchangeRateTable


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

    # ARE-6130 wrapper for the exchange rate table unique currencies function
    def test_unique_currencies(self, reqmock):

        # mock for the Exchange Rate table request
        reqmock.get('https://api/exchange_rate_tables/abc_id', status_code=200, text='{"id":"abc_id"}')

        fx_table = ExchangeRateTable.retrieve('abc_id')
        dir(fx_table)
        type(fx_table.id)
        print(fx_table.id)
        print("This is a print statement in test")
        # mock for the currencies method call
        reqmock.get('https://api/exchange_rate_tables/abc_id/currencies', status_code=200,
                    text='{'
                         '"currencies": '
                         '[ '
                         '{"code": "CAD"}, '
                         '{"code": "EUR"} '
                         ']'
                         '}')
        curr = fx_table.currencies()
        type(curr)
        # f = FooView(id='abc123')
        # assert f.window_var((0.0, 1.0)).num == 1.0

        # reqmock.get('https://api/foo_views/abc123/window_var/0.0_0.5,0.0_1.0',
        #            status_code=200, text='[{"num": 1.0}, {"num": 2.0}]')
        # wm = f.window_var([(0.0, 0.5), (0.0, 1.0)])
        # assert len(wm) == 2
        # assert wm[0].num == 1.0
        # assert wm[1].num == 2.0
        assert 1 == 1
