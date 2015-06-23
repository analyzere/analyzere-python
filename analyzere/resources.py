from analyzere.base_resources import (
    DataResource,
    EmbeddedResource,
    MetricsResource,
    OptimizationResource,
    Resource,
)


# Shared embedded resources

class MonetaryUnit(EmbeddedResource):
    def __init__(self, value, currency, **kwargs):
        super(MonetaryUnit, self).__init__(value=value, currency=currency,
                                           **kwargs)


# Event catalogs

class EventCatalog(DataResource):
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
    pass


class DynamicPortfolioView(MetricsResource):
    pass


# Optimization views

class OptimizationView(OptimizationResource):
    pass


class OptimizationDomain(EmbeddedResource):
    pass
