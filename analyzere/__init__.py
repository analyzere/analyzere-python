# Authentication options

# - 1: Basic Auth
username = ''
password = ''

# - 2: Provide bearer token directly
bearer_auth_token = ''

# - 3: Client Credentials
oauth_token_url = ''
oauth_client_id = ''
oauth_client_secret = ''
oauth_scope = ''

# Config
base_url = 'http://localhost:8000/'
upload_poll_interval = 0.1
one_megabyte = 2**20
upload_chunk_size = 16 * one_megabyte
tls_verify = True
user_agent = 'analyzere-python 0.8-dev'
connection_pool_maxsize = 10
retry_strategy_total = 0
retry_strategy_backoff_factor = 0.1

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
