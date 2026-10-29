"""Application exceptions safe to handle at the UI boundary."""


class InsightSQLError(Exception):
    """Base class for expected application errors."""


class ConfigurationError(InsightSQLError):
    """Application configuration is missing or invalid."""


class ModelProviderError(InsightSQLError):
    """The language model could not generate a query."""


class ModelConfigurationError(InsightSQLError):
    """Natural-language SQL generation is not configured."""


class SQLValidationError(InsightSQLError):
    """Generated SQL does not satisfy the read-only query policy."""


class DatabaseQueryError(InsightSQLError):
    """The database could not execute the approved query."""
