"""Streamlit entry point for InsightSQL."""

from __future__ import annotations

import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from insightsql.config import (  # noqa: E402
    MAX_QUESTION_LENGTH,
    MAX_RESULT_ROWS,
    get_database_path,
    get_openai_api_key,
    get_model_name,
)
from insightsql.database.repository import SQLiteRepository  # noqa: E402
from insightsql.exceptions import InsightSQLError  # noqa: E402
from insightsql.llm.client import OpenAISQLGenerator  # noqa: E402
from insightsql.logging_config import configure_logging  # noqa: E402
from insightsql.services.query_service import QueryService  # noqa: E402

configure_logging()
logger = logging.getLogger(__name__)
MAX_HISTORY_ITEMS = 50

st.set_page_config(page_title="InsightSQL", page_icon="🔎", layout="wide")


def _init_history() -> None:
    if "query_history" not in st.session_state:
        st.session_state.query_history = []


def _add_history(item: dict[str, Any]) -> None:
    st.session_state.query_history.insert(0, item)
    del st.session_state.query_history[MAX_HISTORY_ITEMS:]


def _show_history() -> None:
    history = st.session_state.query_history
    if not history:
        st.caption("Your questions and generated SQL will appear here for this session.")
        return
    for index, item in enumerate(history):
        title = f"{item['time']} — {item['question'][:80]}"
        with st.expander(title, expanded=index == 0):
            st.code(item["sql"], language="sql")
            if item.get("error"):
                st.warning(item["error"])
            elif item.get("columns") is not None:
                st.caption(f"{item['row_count']} row(s)")


def main() -> None:
    _init_history()
    st.title("InsightSQL")
    st.write("Ask a question about your SQLite data and inspect the generated SQL.")

    with st.sidebar:
        st.header("Connection")
        db_path = get_database_path()
        st.code(str(db_path), language="text")
        st.caption(f"Model: {get_model_name()}")
        if st.button("Clear query history", use_container_width=True):
            st.session_state.query_history = []
            st.rerun()

    try:
        api_key = get_openai_api_key()
    except InsightSQLError as error:
        api_key = None
        st.error(str(error))
    if not api_key:
        st.info(
            "Enter a read-only SELECT query to use the database without an API "
            "key. Configure `OPENAI_API_KEY` to enable natural-language questions."
        )

    with st.form("question_form"):
        question = st.text_area(
            "Your question",
            placeholder="For example: How many projects are active?",
            max_chars=MAX_QUESTION_LENGTH,
            height=100,
        )
        submitted = st.form_submit_button(
            "Generate and run SQL",
            type="primary",
        )

    if submitted:
        request_id = uuid.uuid4().hex[:12]
        started = time.monotonic()
        history_item: dict[str, Any] = {
            "time": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M"),
            "question": question.strip(),
            "sql": "",
            "columns": None,
            "row_count": 0,
        }
        try:
            repository = SQLiteRepository(db_path)
            service = QueryService(
                OpenAISQLGenerator(api_key) if api_key else None,
                repository,
            )
            with st.spinner("Generating and safely running your query..."):
                result = service.answer(question)
            history_item.update(
                sql=result.sql,
                columns=result.columns,
                row_count=len(result.rows),
                truncated=result.truncated,
            )
            logger.info(
                "query_completed request_id=%s row_count=%d duration_ms=%d",
                request_id,
                len(result.rows),
                int((time.monotonic() - started) * 1_000),
            )
            st.subheader("Generated SQL")
            st.code(result.sql, language="sql")
            st.subheader("Query results")
            if result.rows:
                st.dataframe(
                    pd.DataFrame(result.rows, columns=result.columns),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("Query completed successfully with no matching rows.")
            if result.truncated:
                st.warning(f"Results were limited to {MAX_RESULT_ROWS:,} rows.")
        except InsightSQLError as error:
            history_item["error"] = str(error)
            logger.warning(
                "query_rejected request_id=%s error_type=%s duration_ms=%d",
                request_id,
                type(error).__name__,
                int((time.monotonic() - started) * 1_000),
            )
            st.error(str(error))
        except Exception as error:
            history_item["error"] = "Something went wrong. Please try again."
            logger.error(
                "unexpected_query_failure request_id=%s error_type=%s",
                request_id,
                type(error).__name__,
            )
            st.error(f"Something went wrong. Please try again. Reference: {request_id}")
        finally:
            _add_history(history_item)

    st.divider()
    st.subheader("Query history")
    _show_history()


if __name__ == "__main__":
    main()
