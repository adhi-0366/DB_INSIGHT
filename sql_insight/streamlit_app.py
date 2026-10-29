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
from insightsql.exceptions import (  # noqa: E402
    DatabaseQueryError,
    InsightSQLError,
)
from insightsql.llm.client import OpenAISQLGenerator  # noqa: E402
from insightsql.logging_config import configure_logging  # noqa: E402
from insightsql.services.query_service import QueryService  # noqa: E402

configure_logging()
logger = logging.getLogger(__name__)
MAX_HISTORY_ITEMS = 50

st.set_page_config(
    page_title="InsightSQL",
    page_icon=":material/query_stats:",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXAMPLE_QUESTIONS = {
    "Projects by status": "How many projects are there in each status?",
    "Team size": "Show the number of employees in each department",
    "Recent projects": "List project names, status, and start date",
}


def _init_history() -> None:
    if "query_history" not in st.session_state:
        st.session_state.query_history = []


def _add_history(item: dict[str, Any]) -> None:
    st.session_state.query_history.insert(0, item)
    del st.session_state.query_history[MAX_HISTORY_ITEMS:]


def _set_example(question: str) -> None:
    st.session_state.question_input = question


def _show_history() -> None:
    history = st.session_state.query_history
    if not history:
        with st.container(border=True):
            st.markdown("#### Your history is clear")
            st.caption("Questions you run during this session will show up here.")
        return
    for index, item in enumerate(history):
        title = f"{item['question'][:72]} · {item['time']}"
        with st.expander(
            title,
            expanded=index == 0,
            icon=":material/check_circle:"
            if not item.get("error")
            else ":material/error:",
        ):
            if item.get("error"):
                st.error(item["error"])
            else:
                st.caption(f"{item['row_count']:,} row(s) returned")
            if item.get("sql"):
                st.code(item["sql"], language="sql")


def main() -> None:
    _init_history()
    st.title("InsightSQL", icon=":material/query_stats:")
    st.caption("Your data, ready to answer. Ask in plain English or write SQL directly.")

    with st.sidebar:
        st.header("Workspace", icon=":material/database:")
        db_path = get_database_path()
        repository = SQLiteRepository(db_path)
        try:
            table_names = sorted(repository.list_tables())
            st.badge("Database connected", icon=":material/check_circle:", color="green")
            st.caption(f"{len(table_names)} available tables")
            with st.expander("Browse schema", icon=":material/table_chart:"):
                for table_name in table_names:
                    st.code(table_name, language="text")
        except DatabaseQueryError as error:
            st.badge("Database unavailable", icon=":material/error:", color="red")
            st.error(str(error))
        st.caption("Database file")
        st.code(db_path.name, language="text")
        st.caption(str(db_path.parent))
        st.caption(f"SQL generation model · {get_model_name()}")
        st.badge("Read-only access", icon=":material/lock:", color="blue")
        st.space("small")
        if st.button(
            "Clear query history",
            icon=":material/delete_sweep:",
            width="stretch",
        ):
            st.session_state.query_history = []
            st.rerun()

    try:
        api_key = get_openai_api_key()
    except InsightSQLError as error:
        api_key = None
        st.error(str(error))
    if not api_key:
        st.caption(
            "Direct read-only SQL works without an API key. Add an OpenAI key "
            "to enable natural-language questions."
        )

    try:
        table_count = len(repository.list_tables())
        database_status = "Online"
    except DatabaseQueryError:
        table_count = 0
        database_status = "Offline"

    metrics_slot = st.empty()

    query_tab, history_tab = st.tabs(
        ["Query workspace", "History"],
        default="Query workspace",
        key="main_view",
    )

    with query_tab:
        with st.container(border=True):
            st.subheader("What would you like to know?", icon=":material/search:")
            st.caption(
                "Choose a starting point or write your own question. "
                "You can also paste a read-only SELECT query."
            )
            example_columns = st.columns(len(EXAMPLE_QUESTIONS))
            for column, (label, example) in zip(
                example_columns, EXAMPLE_QUESTIONS.items(), strict=True
            ):
                column.button(
                    label,
                    icon=":material/arrow_outward:",
                    key=f"example_{label}",
                    on_click=_set_example,
                    args=(example,),
                    width="stretch",
                )

            with st.form("question_form"):
                question = st.text_area(
                    "Ask a question or enter a SELECT query",
                    placeholder=(
                        "e.g. Which projects are active? "
                        "or SELECT * FROM PROJECTS;"
                    ),
                    max_chars=MAX_QUESTION_LENGTH,
                    height=115,
                    key="question_input",
                )
                submitted = st.form_submit_button(
                    "Run query",
                    type="primary",
                    icon=":material/play_arrow:",
                    width="stretch",
                )

        if submitted:
            request_id = uuid.uuid4().hex[:12]
            started = time.monotonic()
            history_item: dict[str, Any] = {
                "time": datetime.now(timezone.utc)
                .astimezone()
                .strftime("%Y-%m-%d %H:%M"),
                "question": question.strip(),
                "sql": "",
                "columns": None,
                "row_count": 0,
            }
            try:
                service = QueryService(
                    OpenAISQLGenerator(api_key) if api_key else None,
                    repository,
                )
                with st.spinner("Working through your query..."):
                    result = service.answer(question)
                history_item.update(
                    sql=result.sql,
                    columns=result.columns,
                    row_count=len(result.rows),
                    truncated=result.truncated,
                )
                st.session_state.last_result = {
                    "question": question.strip(),
                    "sql": result.sql,
                    "columns": result.columns,
                    "rows": result.rows,
                    "row_count": len(result.rows),
                    "truncated": result.truncated,
                }
                logger.info(
                    "query_completed request_id=%s row_count=%d duration_ms=%d",
                    request_id,
                    len(result.rows),
                    int((time.monotonic() - started) * 1_000),
                )
            except InsightSQLError as error:
                st.session_state.pop("last_result", None)
                history_item["error"] = str(error)
                logger.warning(
                    "query_rejected request_id=%s error_type=%s duration_ms=%d",
                    request_id,
                    type(error).__name__,
                    int((time.monotonic() - started) * 1_000),
                )
                st.error(str(error))
            except Exception as error:
                st.session_state.pop("last_result", None)
                history_item["error"] = "Something went wrong. Please try again."
                logger.error(
                    "unexpected_query_failure request_id=%s error_type=%s",
                    request_id,
                    type(error).__name__,
                )
                st.error(
                    f"Something went wrong. Please try again. Reference: {request_id}"
                )
            finally:
                _add_history(history_item)

        last_result = st.session_state.get("last_result")
        if last_result:
            st.space("medium")
            st.subheader("Results", icon=":material/table_view:")
            st.caption(f"Answering: {last_result['question']}")
            with st.container(border=True):
                with st.expander(
                    "Generated SQL",
                    expanded=True,
                    icon=":material/code:",
                ):
                    st.code(last_result["sql"], language="sql")
                if last_result["rows"]:
                    result_frame = pd.DataFrame(
                        last_result["rows"],
                        columns=last_result["columns"],
                    )
                    st.dataframe(
                        result_frame,
                        hide_index=True,
                        width="stretch",
                        height="auto",
                        key="query_results",
                        alt="Rows returned by the latest SQL query",
                    )
                    st.download_button(
                        "Download results as CSV",
                        data=result_frame.to_csv(index=False).encode("utf-8"),
                        file_name="insightsql-results.csv",
                        mime="text/csv",
                        icon=":material/download:",
                    )
                else:
                    st.success(
                        "Query completed successfully with no matching rows.",
                        icon=":material/check_circle:",
                    )
                if last_result["truncated"]:
                    st.warning(
                        f"Results were limited to {MAX_RESULT_ROWS:,} rows.",
                        icon=":material/warning:",
                    )

    with history_tab:
        st.subheader("Your recent queries", icon=":material/history:")
        st.caption("History is saved only for this browser session.")
        _show_history()

    history = st.session_state.query_history
    last_result = st.session_state.get("last_result")
    with metrics_slot.container():
        metric_columns = st.columns(4)
        metric_columns[0].metric(
            "Database",
            database_status,
            icon=":material/database:",
            border=True,
        )
        metric_columns[1].metric(
            "Tables",
            table_count,
            icon=":material/table_chart:",
            border=True,
        )
        metric_columns[2].metric(
            "Queries this session",
            len(history),
            icon=":material/history:",
            border=True,
        )
        metric_columns[3].metric(
            "Latest result",
            f"{last_result['row_count']:,} rows" if last_result else "—",
            icon=":material/query_stats:",
            border=True,
        )


if __name__ == "__main__":
    main()
