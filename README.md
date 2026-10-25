# Persian Text-to-SQL for MariaDB

Generate **MariaDB `SELECT` queries from Persian (Farsi) questions**, entirely with a **local Ollama model**. Choose either **Vanna 2.0 + SQLGlot** or **LlamaIndex + SQLGlot** without changing the rest of your application.

> **SQL generation only.** This package does not connect to MariaDB, run queries, or send database contents to a remote LLM. You supply schema metadata as `.md`, `.sql`, or `.txt`. SQLGlot provides useful structural checks—not a full MariaDB grammar, security sandbox, or guarantee of valid columns.

## Features

- 🇮🇷 Persian natural-language questions, including Persian/Arabic digits and Persian business descriptions.
- 🗄️ MariaDB-focused prompt and schema documentation (English or Persian Markdown).
- 🦙 Local Ollama model, default `gemma4:12b`; configurable model/host.
- 🔁 Two interchangeable providers: **Vanna** or **LlamaIndex**, with the same `generate_sql_sync` / `generate_sql` API.
- 🔎 Shared **SQLGlot** parser, single-statement checks, rejection of recognized writes, `SELECT INTO`, locking reads, dangerous functions, and multiple statements.
- 🛠️ Retry invalid SQL using the previous validation error; configurable context, timeout and output tokens.
- ⚡ Native async completion through LlamaIndex; the Vanna Ollama adapter runs in a worker thread to avoid blocking the async event loop.
- 📦 Separate optional dependencies, online `pip` installation, and a CLI for Windows, Linux, and macOS.
- 🧪 Unit tests that don't need a live Ollama server or MariaDB connection.

## Architecture

```text
Persian user question (e.g. «۱۰ مشتری پرفروش را نشان بده»)
                 +
     examples/schema.md (or your own Markdown schema)
                 |
          shared Persian/MariaDB prompt
                 |
      +----------+-----------+
      |                      |
  Vanna 2.x               LlamaIndex
      |                      |
      +---------+------------+
                |
      Local Ollama (Gemma 4)
                |
      SQLGlot (MySQL parser)
                |
    SELECT SQL  OR  validation failure/retry
```

### Vanna vs LlamaIndex

| | Vanna + SQLGlot | LlamaIndex + SQLGlot |
|---|---|---|
| SQL generation | `OllamaLlmService` | `Ollama.complete()` |
| Async | Worker-thread wrapper around Vanna 2.0.2 adapter | Native `acomplete()` |
| Database connection | None | None |
| Markdown schema | ✅ | ✅ |
| SQLGlot parser | Shared | Shared |
| Additional RAG, memory or agents | **Not enabled** | **Not enabled** |

> This repository uses each framework's **LLM integration**, not Vanna's full agent/database tools or LlamaIndex's text-to-SQL database query engine. That is intentional: **generate SQL without executing it**.

## Requirements

- Python **3.10+** (3.11 or 3.12 recommended); Windows, Linux or macOS.
- An installed and running [Ollama](https://ollama.com/) instance.
- An Ollama model that understands Persian and can produce SQL. Examples use `gemma4:12b`.
- A schema document describing your **actual** MariaDB tables/columns, foreign keys, allowed status values, and date/calendar conventions.

## Install online

The commands below **download dependencies from PyPI** with `pip`. No wheel directory or offline package files are needed. You can install **Vanna only**, **LlamaIndex only**, or **both**.

### Option A — Clone the GitHub repository (recommended)

**Windows CMD:**

```cmd
git clone https://github.com/psohofi/persian-text2sql.git
cd persian-text2sql
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
```

If you already cloned the repository, open CMD inside its folder (the folder containing `pyproject.toml`) and start from `py -m venv .venv`.

**Linux / macOS:**

```bash
git clone https://github.com/psohofi/persian-text2sql.git
cd persian-text2sql
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install **just Vanna + SQLGlot**:

```bash
python -m pip install -e ".[vanna]"
```

Or install **just LlamaIndex + SQLGlot**:

```bash
python -m pip install -e ".[llamaindex]"
```

Install **both backends**:

```bash
python -m pip install -e ".[all]"
```

For both backends **plus the optional FastAPI example**:

```bash
python -m pip install -e ".[all,api]"
```

`-e` installs this project in *editable mode*: changes to its source files are picked up without reinstalling. The dependencies are installed online from PyPI.

### Option B — Install directly from GitHub (without cloning)

If you only want to use the package in another project, install it straight from this repository:

```bash
python -m pip install "persian-mariadb-text2sql[all] @ git+https://github.com/psohofi/persian-text2sql.git"
```

To install just one provider, change `[all]` to `[vanna]` or `[llamaindex]`. Git must be installed and your machine must be able to access GitHub and PyPI. For active development, Option A is usually easier.

### Set up Ollama and the local model

Install [Ollama](https://ollama.com/download) separately, then download the model:

```cmd
ollama pull gemma4:12b
ollama list
```

Ollama normally serves `http://localhost:11434` in the background. If yours is not running, execute `ollama serve` in another terminal.

### Generate SQL from Persian questions

With the repository installed, use the CLI:

```cmd
persian-text2sql --backend vanna --schema examples/schema.md "۱۰ مشتری با بیشترین فروش را نمایش بده"
```

Or:

```cmd
persian-text2sql --backend llamaindex --schema examples/schema.md "مشتریانی که سفارشی ندارند را نمایش بده"
```

If Windows CMD doesn't display Persian text correctly, try Windows Terminal with UTF-8 support, or run one of the Python examples.

## Python integration

### Vanna + SQLGlot

```python
from persian_text2sql import VannaSQLService

service = VannaSQLService(
    schema_path="examples/schema.md",  # replace with your schema.md
    model="gemma4:12b",
    host="http://localhost:11434",
    dialect="MariaDB",
    temperature=0.0,
    num_ctx=8192,
    timeout=900.0,            # helpful for slow local models
    num_predict=1024,        # maximum generated tokens
    max_retries=1,
    debug=False,
)

sql = service.generate_sql_sync("۱۰ مشتری با بیشترین میزان فروش را نشان بده")
print(sql)
```

### LlamaIndex + SQLGlot

```python
from persian_text2sql import LlamaIndexSQLService

service = LlamaIndexSQLService(
    schema_path="examples/schema.md",
    model="gemma4:12b",
    dialect="MariaDB",
    timeout=900.0,
    num_ctx=8192,
    max_retries=1,
)

sql = service.generate_sql_sync("تعداد سفارش‌های تکمیل‌شده هر مشتری را نمایش بده")
print(sql)
```

### Asynchronous applications / FastAPI

```python
# For either service; in `async def` functions, use await.
sql = await service.generate_sql("مشتریان شهر تهران را پیدا کن")
```

For a ready-made FastAPI example:

```cmd
python -m pip install -e ".[llamaindex,api]"
python -m uvicorn examples.fastapi_app:app --host 127.0.0.1 --port 8000
```

`POST http://127.0.0.1:8000/generate-sql` with JSON:

```json
{"question": "۵ مشتری با بیشترین فروش را نمایش بده"}
```

A successful result has the shape `{"question": "...", "sql": "SELECT ...;"}`. The exact SQL depends on your schema and model.

### Dynamic schema override

Pass the schema as a string at construction or override it for one question:

```python
service = LlamaIndexSQLService(schema="CREATE TABLE users (id INT, name VARCHAR(100));")
sql = service.generate_sql_sync("نام کاربران را نمایش بده")

# Use another schema just for this call:
other_sql = service.generate_sql_sync(
    "تمام محصولات را نمایش بده",
    schema="CREATE TABLE products (id INT, name VARCHAR(100));",
)
```

Use **exactly one** of `schema=` or `schema_path=` in the constructor.

## Your `schema.md` matters

The model must know what columns exist, what business terms mean and how values are stored. See [`examples/schema.md`](examples/schema.md) for a bilingual template. In particular, document:

1. **Tables/columns and types** (`customers.id`, `orders.total_amount`, ...).
2. **JOIN relationships** and primary/foreign keys.
3. **Real stored enum values** (`status = 'completed'`, not Persian text unless actually stored that way).
4. **Business rules**: which statuses count as revenue, units/currency, cancellations.
5. **Calendar/timezone**: Gregorian vs Jalali, whether timestamps are UTC/local.
6. **Synonyms in Persian**: «فروش», «خرید», «مبلغ سفارش», etc.

A schema can be Markdown, raw DDL or plain text. The file is read as UTF-8 (including UTF-8 with BOM); its extension is not significant. Large schemas may be slow because this project sends the **entire schema** with each question. A retrieval/indexing step is **not included** in this first release.

> Example SQL is illustrative; no SQL is verified against an actual MariaDB server. Ambiguous Jalali/Gregorian phrases should be clarified or specified in your schema rather than guessed.

## API reference

Both services accept the same arguments:

| Parameter | Default | Description |
|---|---|---|
| `schema_path` / `schema` | None | Required: exactly one UTF-8 schema source |
| `model` | `gemma4:12b` | Exact local Ollama model tag |
| `host` | `http://localhost:11434` | Ollama API URL |
| `dialect` | `MariaDB` | This version is MariaDB-specific |
| `temperature` | `0.0` | Generation randomness |
| `num_ctx` | `8192` | Ollama context window; increase only if needed |
| `timeout` | `900.0` | HTTP timeout in seconds |
| `num_predict` | `1024` | Ollama maximum output token count |
| `max_retries` | `1` | Additional retries after invalid SQL (not network retries) |
| `debug` | `False` | Log raw model replies; avoid logging sensitive schemas/queries |

Methods:

- `service.generate_sql_sync(question: str, schema: str | None = None) -> str`
- `await service.generate_sql(question: str, schema: str | None = None) -> str`

Exceptions:

- `SQLCannotAnswerError`: model returned `CANNOT_ANSWER`.
- `SQLGenerationError`: SQLGlot validation/extraction failed after retries.
- `ModelRequestError`: Ollama request failed or timed out.
- `ValueError`: invalid question, schema or constructor arguments.

## Troubleshooting

**`Ollama request failed: timeout`**

- Run `ollama run gemma4:12b "SELECT 1"` to isolate Ollama from Python.
- Check `ollama ps` for CPU/GPU usage.
- Try `num_ctx=4096` and a short schema while testing; large prompts are expensive.
- Raise `timeout` if model inference is slow; reducing `num_predict` may help avoid overly long output.
- `max_retries` only retries **invalid SQL**, not a network timeout.

**`SQLGenerationError` / `Only SELECT queries are accepted`**

- Set `debug=True`, configure Python logging, and inspect what Gemma returned.
- Make sure schema names and JOIN keys are correct. Models sometimes prepend explanations despite instructions.
- SQLGlot uses the `mysql` dialect as a MariaDB approximation; MariaDB-specific syntax may parse differently.

**`ModuleNotFoundError` for Vanna/LlamaIndex**

- Install the correct package extra (`.[vanna]`, `.[llamaindex]` or `.[all]`).
- Use the same Python interpreter for `pip` and your application.

**Persian text does not match database records**

- Document whether the actual stored string is `'تهران'`, `'Tehran'`, or a numeric city ID.
- Ensure your MariaDB connection/columns use an appropriate Unicode character set (for execution performed outside this package).

## Security and accuracy notes

**Do not assume generated SQL is safe or correct.** SQLGlot identifies many invalid/unsafe structures, but cannot prove that all MariaDB queries are read-only or correct, particularly when functions, views, stored functions or dialect-specific syntax are involved. This project intentionally **does not execute SQL**.

If you later add a database executor: use a **restricted read-only MariaDB user**, forbid file and stored-function privileges where possible, enforce timeouts and result limits in the database, validate tables/columns against the catalog, and review queries before execution. Never run model-generated SQL with a DBA account. Parser validation is not equivalent to a security boundary.

No LLM accuracy benchmark has been established here. Compare the two backends with the **same schema and question set**; the quality may depend more on Gemma, schema documentation and examples than on the framework.

## Run the tests

```cmd
python -m pip install -e ".[dev]"
python -m pytest -q
```

Tests use fake model responses and test SQL extraction/validation locally; they do **not** require Ollama or MariaDB. For integration testing, install one provider and run `examples/use_vanna.py` or `examples/use_llamaindex.py` with your Ollama server running.

GitHub Actions runs the dependency-light test suite on supported Python versions.

## Directory structure

```text
persian-mariadb-text2sql/
├── .github/workflows/tests.yml
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── src/persian_text2sql/
│   ├── __init__.py
│   ├── base.py                   # schema, retries, shared API logic
│   ├── cli.py                    # persian-text2sql command
│   ├── exceptions.py
│   ├── llamaindex_service.py     # LlamaIndex + Ollama
│   ├── prompt.py                 # Persian/MariaDB SQL instructions
│   ├── schema.py                 # UTF-8 Markdown/DDL loading
│   ├── validation.py             # SQLGlot parser & AST checks
│   └── vanna_service.py          # Vanna 2.0.2 + Ollama
├── examples/
│   ├── schema.md
│   ├── use_vanna.py
│   ├── use_llamaindex.py
│   ├── use_async.py
│   └── fastapi_app.py
└── tests/
    ├── test_validation.py
    └── test_services.py
```
