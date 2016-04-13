username = ''
password = ''
base_url = 'http://localhost:8000/'
upload_poll_interval = 0.1
upload_chunk_size = 16 * (1 << 20)
tls_verify = True

from analyzere.resources import (  # noqa
    AnalysisProfile,
    Distribution,
    DynamicPortfolioView,
    EventCatalog,
    ExchangeRateProfile,
    ExchangeRateSelectionRule,
    ExchangeRateTable,
    InuringTerms,
    Layer,
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
