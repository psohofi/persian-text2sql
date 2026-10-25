"""Conservative structural checks for generated SELECT SQL using SQLGlot.

This is NOT a complete MariaDB syntax checker, SQL firewall or permission guard.
Use a read-only MariaDB account, and limit time/rows before execution elsewhere.
"""

import re

from sqlglot import exp, parse
from sqlglot.errors import ErrorLevel, ParseError

from .exceptions import SQLCannotAnswerError, SQLGenerationError

_FORBIDDEN_FUNCS = {
    "LOAD_FILE", "SLEEP", "BENCHMARK", "GET_LOCK", "RELEASE_LOCK",
    "IS_FREE_LOCK", "IS_USED_LOCK", "SYS_EVAL", "SYS_EXEC",
}

# SQLGlot expression names vary among versions: use only installed types.
_BLOCKED_NAMES = (
    "DML", "DDL", "Command", "Into", "Lock", "Transaction",
    "Copy", "LoadData", "Execute", "Grant", "Revoke",
)


def extract_sql(raw: str) -> str:
    """Remove common Gemma response wrappers without modifying SQL literals."""
    if not isinstance(raw, str) or not raw.strip():
        raise SQLGenerationError("Ollama returned an empty non-SQL response.")
    value = raw.replace("\ufeff", "").strip()
    value = re.sub(
        r"<think\b[^>]*>.*?</think\s*>", "", value,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()
    if re.search(r"</?think\b", value, flags=re.IGNORECASE):
        raise SQLGenerationError("Incomplete <think> block in model output.")
    if re.fullmatch(r"CANNOT_ANSWER\s*\.?", value, flags=re.IGNORECASE):
        raise SQLCannotAnswerError("Schema does not support this question.")

    fenced = re.findall(
        r"```(?:sql|mysql|mariadb)?[ \t]*\r?\n(.*?)```", value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if fenced:
        if len(fenced) != 1:
            raise SQLGenerationError("Model returned multiple SQL code blocks.")
        value = fenced[0].strip()
    else:
        # Some models prepend a Persian or English introductory sentence.
        first = re.search(r"(?im)^[ \t]*(?:SQL[ \t]*:[ \t]*)?(SELECT|WITH)\b", value)
        if first is None:
            first = re.search(r"\b(SELECT|WITH)\b", value, flags=re.IGNORECASE)
        if first is None:
            raise SQLGenerationError("No SELECT or WITH query in model output.")
        value = value[first.start(1):].strip()

    if not value:
        raise SQLGenerationError("Extracted SQL is empty.")
    if re.fullmatch(r"CANNOT_ANSWER\s*\.?", value, flags=re.IGNORECASE):
        raise SQLCannotAnswerError("Schema does not support this question.")
    return value


def validate_sql(sql: str) -> str:
    """Check that SQLGlot parses one top-level read SELECT/set expression.

    Parse using `mysql` because SQLGlot has no dedicated MariaDB dialect.
    Returned SQL is *not* transpiled, preserving Persian string literals.
    """
    if not re.match(r"(?is)^\s*(SELECT|WITH)\b", sql):
        raise SQLGenerationError("Only SELECT / WITH ... SELECT SQL is accepted.")

    try:
        statements = [tree for tree in parse(
            sql, read="mysql", error_level=ErrorLevel.RAISE
        ) if tree is not None]
    except ParseError as exc:
        raise SQLGenerationError(f"SQLGlot MySQL parse failed: {exc}") from exc

    if len(statements) != 1:
        raise SQLGenerationError(
            f"Expected exactly one SQL statement; received {len(statements)}."
        )
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.SetOperation)):
        raise SQLGenerationError(
            f"Expected a read SELECT statement; found {type(tree).__name__}."
        )

    blocked_types = tuple(
        cls for name in _BLOCKED_NAMES
        if isinstance((cls := getattr(exp, name, None)), type)
    )
    for node in tree.walk():
        if blocked_types and isinstance(node, blocked_types):
            raise SQLGenerationError(f"Prohibited SQL operation: {type(node).__name__}.")
        if isinstance(node, exp.Anonymous) and node.name.upper() in _FORBIDDEN_FUNCS:
            raise SQLGenerationError(f"Prohibited SQL function: {node.name}.")

    # Reject user-variable assignments, which can alter session state.
    # This is a conservative supplementary check (not a full security scanner).
    if ":=" in sql:
        raise SQLGenerationError("User-variable assignments (:=) are not permitted.")

    return sql.rstrip().rstrip(";").rstrip() + ";"


def extract_and_validate(raw: str) -> str:
    return validate_sql(extract_sql(raw))
