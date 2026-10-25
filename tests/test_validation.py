import pytest

from persian_text2sql.exceptions import SQLCannotAnswerError, SQLGenerationError
from persian_text2sql.validation import extract_sql, validate_sql, extract_and_validate


@pytest.mark.parametrize("raw, expected", [
    ("SELECT * FROM customers;", "SELECT * FROM customers;"),
    ("```sql\nSELECT city FROM customers WHERE city='تهران';\n```",
     "SELECT city FROM customers WHERE city='تهران';"),
    ("<think>some reasoning</think>\nSELECT COUNT(*) FROM orders;",
     "SELECT COUNT(*) FROM orders;"),
    ("کوئری:\nSELECT * FROM customers LIMIT 10;", "SELECT * FROM customers LIMIT 10;"),
    ("WITH c AS (SELECT id FROM customers) SELECT * FROM c;",
     "WITH c AS (SELECT id FROM customers) SELECT * FROM c;"),
    ("SELECT id FROM customers UNION SELECT customer_id FROM orders;",
     "SELECT id FROM customers UNION SELECT customer_id FROM orders;"),
])
def test_select_and_extract(raw, expected):
    assert extract_and_validate(raw) == expected


@pytest.mark.parametrize("sql", [
    "DELETE FROM customers WHERE id = 1;",
    "SELECT id FROM customers; DROP TABLE customers;",
    "SELECT * FROM customers FOR UPDATE;",
    "SELECT * FROM customers INTO OUTFILE '/tmp/test.csv';",
    "SELECT SLEEP(5) FROM customers;",
    "SELECT @n := 1 FROM customers;",
    "SELECT (1 + FROM customers;",
])
def test_reject_unsafe_or_invalid(sql):
    with pytest.raises(SQLGenerationError):
        validate_sql(sql)


def test_cannot_answer():
    with pytest.raises(SQLCannotAnswerError):
        extract_sql("CANNOT_ANSWER")


def test_missing_query():
    with pytest.raises(SQLGenerationError):
        extract_sql("نمی‌توانم این کار را انجام دهم")
