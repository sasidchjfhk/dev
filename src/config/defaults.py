"""Default configuration values for the application."""

# Default search engine to use if none is specified
DEFAULT_SEARCH_ENGINE = "google"  # Options: "google", "bing", "duckduckgo"

# Default AI model to use if none is specified
DEFAULT_AI_MODEL = "gpt-4o-mini"

# API endpoints
API_BASE_URL = "http://localhost:1337"

# Timeout settings
REQUEST_TIMEOUT = 30  # seconds

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
