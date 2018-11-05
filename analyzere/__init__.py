username = ''
password = ''
base_url = 'http://localhost:8000/'
upload_poll_interval = 0.1
one_megabyte = 2**20
upload_chunk_size = 16 * one_megabyte
tls_verify = True
user_agent = 'analyzere-python 0.5.5-dev'

from analyzere.resources import (  # noqa
    AnalysisProfile,
    Distribution,
    DynamicPortfolioView,
    EventCatalog,
    ExchangeRateProfile,
    ExchangeRateSelectionRule,
    ExchangeRateTable,
    Fee,
    FeeReference,
    InuringTerms,
    Layer,
    LayerPolicy,
    LayerView,
    LossAttribute,
    LossFilter,
    LossSet,
    LossSetProfile,
    MonetaryUnit,
    OptimizationDomain,
    OptimizationView,
    Portfolio,
    PortfolioView,
    Reinstatement,
    Simulation,
    Treaty,
)

from analyzere.errors import (  # noqa
    AuthenticationError,
    InvalidRequestError,
    MissingIdError,
    ServerError,
)
