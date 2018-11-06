import warnings

from analyzere.base_resources import (
    DataResource,
    EmbeddedResource,
    MetricsResource,
    Resource,
    load_reference,
    to_dict,
    convert_to_analyzere_object, NestedResource)
from analyzere.requestor import request


# Shared embedded resources

class MonetaryUnit(EmbeddedResource):
    def __init__(self, value, currency, **kwargs):
        super(MonetaryUnit, self).__init__(value=value, currency=currency,
                                           **kwargs)


# Event catalogs

class EventCatalog(DataResource):
    def profile(self):
        path = '%s/profile' % self._get_path(self.id)
        resp = request('get', path)
        return convert_to_analyzere_object(resp)


# Exchange rate tables

class ExchangeRateTable(DataResource):
    pass


class ExchangeRateSelectionRule(EmbeddedResource):
    pass


class ExchangeRateProfile(Resource):
    pass


# Distributions

class Distribution(DataResource):
    pass


# Loss sets

class LossSet(DataResource):
    pass


class LossSetProfile(EmbeddedResource):
    pass


class InuringTerms(EmbeddedResource):
    pass


class Treaty(EmbeddedResource):
    pass


# Layers

class Fee(EmbeddedResource):
    pass


class FeeReference(EmbeddedResource):
    # premiums
    PREMIUM = {'ref': ['Layer', 'Premium']}
    REINSTATEMENT_PREMIUM = {'ref': ['Layer', 'ReinstatementPremium']}
    REINSTATEMENT_BROKERAGE = {'ref': ['Layer', 'ReinstatementBrokerage']}

    # losses
    LOSSES = {'ref': ['Layer', 'Losses']}

    @staticmethod
    def from_fee(fee):
        return {'ref': ['Layer', 'Fees', fee.name]}


class LayerPolicy(EmbeddedResource):
    def __init__(self, transform_records, forward_records, **kwargs):
        super(LayerPolicy, self).__init__(
            transform_records=transform_records,
            forward_records=forward_records,
            **kwargs
        )


class Reinstatement(EmbeddedResource):
    pass


class Layer(Resource):
    pass


# Portfolios

class Portfolio(Resource):
    pass


# Simulations

class Simulation(DataResource):
    pass


# Loss attributes

class LossAttribute(Resource):
    pass


# Loss filters

class LossFilter(Resource):
    pass


# Layer views

class LayerView(MetricsResource):
    pass


class AnalysisProfile(Resource):
    pass


# Portfolio views

class PortfolioView(MetricsResource):
    def marginal(self, layer_views_to_add, layer_views_to_remove):
        path = 'portfolio_view_marginals'
        data = request('post', path, data={
            'portfolio_view_id': to_dict(self.reference()),
            'add_layer_view_ids': [to_dict(lv.reference()) for lv in layer_views_to_add],
            'remove_layer_view_ids': [to_dict(lv.reference()) for lv in layer_views_to_remove]
        })
        return load_reference('portfolio_views', data['portfolio_view']['ref_id'])


class DynamicPortfolioView(MetricsResource):
    pass


# Optimization views

class OptimizationView(Resource):
    def result(self):
        warnings.warn(
            "result() is deprecated, use candidates() instead to page over results",
            DeprecationWarning
        )
        path = '{}/result'.format(self._get_path(self.id))
        resp = request('get', path)
        return convert_to_analyzere_object(resp)

    def initial_metrics(self):
        """
        The name of this method is chosen to avoid overlap with the initial_portfolio_metrics property of the
        OptimizationView
        """
        path = '{}/initial_portfolio_metrics'.format(self._get_path(self.id))
        resp = request('get', path)
        return convert_to_analyzere_object(resp)

    def candidates(self, index=None):
        if index is None:
            path = '{}/candidates'.format(self._get_path(self.id))
        else:
            try:
                index = int(index)
            except ValueError:
                raise Exception('index argument provided to OptimizationView.candidates() must be an integer')
            path = '{}/candidates/{}'.format(self._get_path(self.id), index)
        resp = request('get', path)
        return convert_to_analyzere_object(resp, Candidate, optimization_view_id=self.id)


class OptimizationDomain(EmbeddedResource):
    pass


class Candidate(NestedResource):

    def __init__(self, optimization_view_id=None, **kwargs):
        self.optimization_view_id = optimization_view_id
        super(Candidate, self).__init__(**kwargs)

    def portfolio_view(self):
        path = '{}/candidates/{}/portfolio_view'.format(OptimizationView._get_path(self.optimization_view_id),
                                                        self.index)
        resp = request('get', path)
        return convert_to_analyzere_object(resp, PortfolioView)
