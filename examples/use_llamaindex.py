"""Run: python examples/use_llamaindex.py (after pip install -e '.[llamaindex]')"""
from pathlib import Path

from persian_text2sql import LlamaIndexSQLService

ROOT = Path(__file__).resolve().parent
service = LlamaIndexSQLService(
    schema_path=ROOT / "schema.md",
    model="gemma4:12b",
    dialect="MariaDB",
    timeout=900.0,
    num_ctx=8192,
    num_predict=1024,
    max_retries=1,
)

sql = service.generate_sql_sync("مشتریانی که هیچ سفارشی ندارند را نمایش بده")
print(sql)
