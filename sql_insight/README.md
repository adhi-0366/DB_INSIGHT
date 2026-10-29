# InsightSQL

InsightSQL is a Streamlit application for asking natural-language questions
about an approved SQLite database. It generates SQL using OpenAI GPT, validates
the generated query, executes read-only queries, displays results and SQL, and
keeps a bounded query history in the current Streamlit session.

## Requirements

- Python 3.11 or newer
- An OpenAI API key
- A SQLite database (by default, the sibling
  `../DB_INSIGHT/employee_management.db`)

## Run locally

From this directory, in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:OPENAI_API_KEY = "your-api-key"
py -m streamlit run streamlit_app.py
```

Alternatively, create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-api-key"
```

The secrets file is excluded from version control. To use a different database:

```powershell
$env:INSIGHTSQL_DB_PATH = "D:\path\to\database.db"
```

If OpenAI returns an authentication, quota/rate-limit, connectivity, or model
availability error, the app displays a specific message. Verify that the key
is valid and that the configured model is available to your account.

## Security behavior

- Only a single `SELECT` query is accepted. `WITH ... SELECT` and read-only
  set operations are allowed; DDL, DML, `PRAGMA`, multiple statements,
  unknown tables, and extension/file functions are rejected.
- You can enter a read-only SQL query directly without an OpenAI key. A key is
  required only when asking a natural-language question.
- SQL is parsed using SQLGlot, then independently restricted by a SQLite
  authorizer and a `mode=ro` connection with `query_only` enabled.
- Queries have a five-second execution budget and return at most 1,000 rows.
- Prompts, generated SQL, result values, and API keys are not written to logs.
- Query history is limited to 50 entries and held only in Streamlit session
  state; it is not persisted to the database.

## Tests

```powershell
py -m pytest
```
