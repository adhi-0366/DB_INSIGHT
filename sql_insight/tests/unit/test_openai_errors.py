from __future__ import annotations

from types import SimpleNamespace
from typing import Callable

import httpx
import pytest
from openai import AuthenticationError, RateLimitError

from insightsql.exceptions import ModelProviderError
from insightsql.llm.client import OpenAISQLGenerator


def _http_response(status_code: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return httpx.Response(status_code, request=request)


@pytest.mark.parametrize(
    ("error_factory", "message"),
    [
        (
            lambda: AuthenticationError(
                "Unauthorized",
                response=_http_response(401),
                body={"error": "secret provider detail"},
            ),
            "OpenAI rejected the API key",
        ),
        (
            lambda: RateLimitError(
                "Rate limited",
                response=_http_response(429),
                body={"error": "secret provider detail"},
            ),
            "usage quota",
        ),
    ],
)
def test_provider_errors_have_actionable_redacted_messages(
    error_factory: Callable[[], Exception], message: str
) -> None:
    generator = OpenAISQLGenerator("test-key")

    def fail_request(**kwargs: object) -> None:
        raise error_factory()

    generator._client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=fail_request)
        )
    )

    with pytest.raises(ModelProviderError, match=message) as error:
        generator.generate_sql("How many projects?", "PROJECTS(project_id)")

    assert "secret provider detail" not in str(error.value)
