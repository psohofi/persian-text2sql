"""Tests use fake LLM integrations; no Ollama or database is required."""

import asyncio
import sys
import types
from unittest.mock import MagicMock

import pytest

from persian_text2sql import SQLCannotAnswerError, SQLGenerationError
from persian_text2sql.base import BaseSQLService


SCHEMA = "CREATE TABLE customers (id INT PRIMARY KEY, city VARCHAR(100));"


class DummyService(BaseSQLService):
    def __init__(self, responses, **kwargs):
        super().__init__(schema=SCHEMA, **kwargs)
        self._responses = iter(responses)
        self.prompts = []

    def ask(self, prompt):
        self.prompts.append(prompt)
        return next(self._responses)

    async def aask(self, prompt):
        self.prompts.append(prompt)
        return next(self._responses)

    def generate_sql_sync(self, question):
        return self._generate_sync(question, None, self.ask)

    async def generate_sql(self, question):
        return await self._generate_async(question, None, self.aask)


def test_retry_and_persian_prompt():
    s = DummyService(["wrong answer", "SELECT city FROM customers WHERE city='تهران';"], max_retries=1)
    sql = s.generate_sql_sync("مشتریان تهران را نشان بده")
    assert "'تهران'" in sql
    assert len(s.prompts) == 2
    assert "مشتریان تهران" in s.prompts[0]
    assert "previous response" in s.prompts[1]


def test_persistent_invalid_output():
    s = DummyService(["nonsense"], max_retries=0)
    with pytest.raises(SQLGenerationError):
        s.generate_sql_sync("سلام")


def test_cannot_answer_no_retry():
    s = DummyService(["CANNOT_ANSWER", "SELECT 1;"], max_retries=2)
    with pytest.raises(SQLCannotAnswerError):
        s.generate_sql_sync("سؤال بدون جدول")
    assert len(s.prompts) == 1


def test_async():
    s = DummyService(["SELECT * FROM customers LIMIT 10;"], max_retries=0)
    assert asyncio.run(s.generate_sql("۱۰ مشتری")) == "SELECT * FROM customers LIMIT 10;"


def test_schema_overrides_and_markdown(tmp_path):
    from persian_text2sql.schema import load_schema
    p = tmp_path / "schema.md"
    p.write_text("# شِما\n| id | INT |", encoding="utf-8-sig")
    assert "شِما" in load_schema(schema_path=p, schema=None)
    with pytest.raises(ValueError):
        load_schema(schema_path=p, schema="also given")


def test_backend_class_imports():
    from persian_text2sql import LlamaIndexSQLService, VannaSQLService
    assert LlamaIndexSQLService.__name__ == "LlamaIndexSQLService"
    assert VannaSQLService.__name__ == "VannaSQLService"
