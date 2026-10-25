"""Run: python examples/use_async.py; switch backend if desired."""
import asyncio
from pathlib import Path

from persian_text2sql import LlamaIndexSQLService  # or VannaSQLService


async def main():
    service = LlamaIndexSQLService(
        schema_path=Path(__file__).with_name("schema.md"),
        model="gemma4:12b",
    )
    sql = await service.generate_sql("سفارش‌های شهر تهران را نشان بده")
    print(sql)


if __name__ == "__main__":
    asyncio.run(main())
