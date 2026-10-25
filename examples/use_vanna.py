"""Run: python examples/use_vanna.py (after pip install -e '.[vanna]')"""
from pathlib import Path

from persian_text2sql import VannaSQLService

ROOT = Path(__file__).resolve().parent
service = VannaSQLService(
    schema_path=ROOT / "schema.md",
    model="gemma4:12b",
    dialect="MariaDB",
    timeout=900.0,
    num_ctx=8192,
    num_predict=1024,
    max_retries=1,
    debug=False,
)

sql = service.generate_sql_sync("۱۰ مشتری با بیشترین میزان فروش را نشان بده")
print(sql)
