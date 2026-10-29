from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[2] / "streamlit_app.py"


def test_app_renders_dashboard_and_runs_direct_select() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()

    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Query workspace", "History"]
    assert any(metric.label == "Tables" and metric.value == "4" for metric in app.metric)

    app.text_area[0].set_value("SELECT * FROM PROJECTS;")
    app.button[3].click().run()

    assert not app.exception
    assert not app.error
    assert len(app.dataframe) == 1
    assert any(
        metric.label == "Latest result" and metric.value == "10 rows"
        for metric in app.metric
    )
    assert "SELECT * FROM PROJECTS" in "\n".join(
        str(code.value) for code in app.code
    ).upper()


def test_app_displays_read_only_validation_error() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    app.text_area[0].set_value("DROP TABLE PROJECTS")
    app.button[3].click().run()

    assert not app.exception
    assert any("read-only SELECT" in error.value for error in app.error)
    assert len(app.dataframe) == 0


def test_starter_question_fills_query_box() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    app.button[0].click().run()

    assert app.text_area[0].value == "How many projects are there in each status?"
