"""Shared retry, schema and prompt logic for the two backends."""

import logging
from typing import Optional, Union
from pathlib import Path

from .exceptions import SQLCannotAnswerError, SQLGenerationError
from .prompt import build_prompt
from .schema import load_schema, prepare_question
from .validation import extract_and_validate

logger = logging.getLogger(__name__)


class BaseSQLService:
    def __init__(
        self,
        schema_path: Optional[Union[str, Path]] = None,
        schema: Optional[str] = None,
        dialect: str = "MariaDB",
        max_retries: int = 1,
        debug: bool = False,
    ) -> None:
        self.schema = load_schema(schema_path=schema_path, schema=schema)
        if not isinstance(dialect, str) or dialect.lower() != "mariadb":
            raise ValueError("This project currently supports dialect='MariaDB' only.")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0.")
        self.dialect = dialect
        self.max_retries = max_retries
        self.debug = debug

    def _inputs(self, question: str, schema: Optional[str]) -> tuple[str, str]:
        q = prepare_question(question)
        s = self.schema if schema is None else schema.strip()
        if not s:
            raise ValueError("Schema override must not be empty.")
        return q, s

    def _prompt(self, question: str, schema: str, feedback: str) -> str:
        return build_prompt(
            dialect=self.dialect, schema=schema, question=question, repair=feedback,
        )

    def _attempt(self, raw: str, attempt_number: int) -> str:
        if self.debug:
            logger.warning("Model raw response (attempt %d): %s", attempt_number, raw)
        return extract_and_validate(raw)

    @staticmethod
    def _repair_message(error: SQLGenerationError, previous_output: str) -> str:
        return (
            "Your previous response did not pass SQL validation. "
            "Fix it and return ONLY one correct MariaDB SELECT statement.\n"
            f"Validation problem: {str(error)[:1000]}\n"
            f"Previous output: {previous_output[:1600]}"
        )

    def _generate_sync(self, question: str, schema: Optional[str], ask) -> str:
        q, s = self._inputs(question, schema)
        feedback = ""
        last_error: Optional[SQLGenerationError] = None
        for attempt in range(1, self.max_retries + 2):
            raw = ask(self._prompt(q, s, feedback))
            try:
                return self._attempt(raw, attempt)
            except SQLCannotAnswerError:
                raise
            except SQLGenerationError as exc:
                last_error = exc
                if self.debug:
                    logger.warning("SQL rejected on attempt %d: %s", attempt, exc)
                feedback = self._repair_message(exc, raw)
        raise SQLGenerationError(
            f"SQL generation failed after {self.max_retries + 1} attempt(s). "
            f"Last validation error: {last_error}"
        )

    async def _generate_async(self, question: str, schema: Optional[str], ask) -> str:
        q, s = self._inputs(question, schema)
        feedback = ""
        last_error: Optional[SQLGenerationError] = None
        for attempt in range(1, self.max_retries + 2):
            raw = await ask(self._prompt(q, s, feedback))
            try:
                return self._attempt(raw, attempt)
            except SQLCannotAnswerError:
                raise
            except SQLGenerationError as exc:
                last_error = exc
                if self.debug:
                    logger.warning("SQL rejected on attempt %d: %s", attempt, exc)
                feedback = self._repair_message(exc, raw)
        raise SQLGenerationError(
            f"SQL generation failed after {self.max_retries + 1} attempt(s). "
            f"Last validation error: {last_error}"
        )
