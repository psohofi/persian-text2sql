"""Schema loading and input handling."""

from pathlib import Path
from typing import Optional, Union

PathLike = Union[str, Path]


def load_schema(*, schema_path: Optional[PathLike], schema: Optional[str]) -> str:
    if (schema_path is None) == (schema is None):
        raise ValueError("Provide exactly one of schema_path or schema.")
    if schema_path is not None:
        schema = Path(schema_path).read_text(encoding="utf-8-sig")
    if not isinstance(schema, str) or not schema.strip():
        raise ValueError("Schema must contain non-empty UTF-8 text.")
    return schema.strip()


def prepare_question(question: str) -> str:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string.")
    return question.strip()
