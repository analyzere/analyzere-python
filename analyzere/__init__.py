# Authentication options

# - 1: Basic Auth
username = ''
password = ''

# - 2: Provide bearer token directly
bearer_auth_token = ''

# - 3: Client Credentials
okta_token_url = ''
okta_client_id = ''
okta_client_secret = ''
okta_m2m_scope = ''

# Config
base_url = 'http://localhost:8000/'
upload_poll_interval = 0.1
one_megabyte = 2**20
upload_chunk_size = 16 * one_megabyte
tls_verify = True
user_agent = 'analyzere-python 0.7.1-dev'

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
