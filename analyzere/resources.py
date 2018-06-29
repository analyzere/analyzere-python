from analyzere.base_resources import (
    DataResource,
    EmbeddedResource,
    EventCatalogResource,
    MetricsResource,
    OptimizationResource,
    Resource,
    load_reference,
    to_dict,
)
from analyzere.requestor import request


# Shared embedded resources

class MonetaryUnit(EmbeddedResource):
    def __init__(self, value, currency, **kwargs):
        super(MonetaryUnit, self).__init__(value=value, currency=currency,
                                           **kwargs)


# Event catalogs

class EventCatalog(EventCatalogResource):
    pass


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
    PREMIUM = {'ref': ['layer', 'premium']}
    REINSTATEMENT_PREMIUM = {'ref': ['layer', 'reinstatement_premium']}

    # losses
    LOSSES = {'ref': ['layer', 'losses']}

    @staticmethod
    def from_fee(fee):
        return {'ref': ['layer', 'fees', fee.name]}


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

class OptimizationView(OptimizationResource):
    pass


class OptimizationDomain(EmbeddedResource):
    pass
