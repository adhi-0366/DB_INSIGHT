"""OpenAI SQL generation adapter."""

from __future__ import annotations

import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from insightsql.config import get_model_name
from insightsql.exceptions import ModelProviderError

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You generate SQL for a read-only SQLite analytics application.
Return exactly one SQL SELECT query and no markdown or explanation.
Use only the tables and columns in the supplied schema.
Never generate writes, schema changes, PRAGMA, ATTACH, or extension functions.
If the question cannot be answered from the schema, return: SELECT 1 WHERE 0;
Do not include sensitive sample values in your answer."""


class OpenAISQLGenerator:
    """Generate SQL with OpenAI without granting the model database access."""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self._client = OpenAI(api_key=api_key, timeout=30.0, max_retries=2)
        self._model = model or get_model_name()

    def generate_sql(self, question: str, schema_context: str) -> str:
        """Return candidate SQL; the caller must still validate it."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Schema:\n{schema_context}\n\nQuestion:\n{question}",
                    },
                ],
            )
            if not response.choices:
                raise ModelProviderError("The SQL generator returned an empty response.")
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise ModelProviderError("The SQL generator returned an empty response.")
            return self._remove_code_fence(content.strip())
        except ModelProviderError:
            raise
        except AuthenticationError as error:
            logger.warning("model_authentication_failed")
            raise ModelProviderError(
                "OpenAI rejected the API key. Check OPENAI_API_KEY and try again."
            ) from error
        except RateLimitError as error:
            logger.warning("model_rate_limit_or_quota_error")
            raise ModelProviderError(
                "OpenAI rate limit or usage quota reached. Check your OpenAI "
                "billing and usage limits, then try again."
            ) from error
        except APITimeoutError as error:
            logger.warning("model_request_timed_out")
            raise ModelProviderError(
                "The OpenAI request timed out. Check your connection and try again."
            ) from error
        except APIConnectionError as error:
            logger.warning("model_connection_failed")
            raise ModelProviderError(
                "Could not connect to OpenAI. Check your internet connection and try again."
            ) from error
        except BadRequestError as error:
            logger.warning("model_request_rejected status_code=%s", error.status_code)
            raise ModelProviderError(
                "OpenAI rejected the request. Check that the configured model is "
                "available to your account."
            ) from error
        except APIStatusError as error:
            logger.warning("model_provider_error status_code=%s", error.status_code)
            raise ModelProviderError(
                f"OpenAI returned an error (HTTP {error.status_code}). Please try again."
            ) from error
        except OpenAIError as error:
            logger.warning("model_request_failed error_type=%s", type(error).__name__)
            raise ModelProviderError(
                "The SQL service is temporarily unavailable. Please try again."
            ) from error

    @staticmethod
    def _remove_code_fence(content: str) -> str:
        """Remove a single optional Markdown SQL code fence."""
        if not content.startswith("```"):
            return content
        lines = content.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
        return content
