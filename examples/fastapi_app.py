"""Optional API: pip install -e '.[llamaindex,api]'
Run from repo root: uvicorn examples.fastapi_app:app --port 8000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from persian_text2sql import (
    LlamaIndexSQLService,
    ModelRequestError,
    SQLCannotAnswerError,
    SQLGenerationError,
)

app = FastAPI(title="Persian MariaDB Text-to-SQL")
service = LlamaIndexSQLService(
    schema_path=Path(__file__).with_name("schema.md"),
    model="gemma4:12b",
)


class GenerateRequest(BaseModel):
    question: str = Field(min_length=1)


@app.post("/generate-sql")
async def generate_sql(request: GenerateRequest):
    try:
        sql = await service.generate_sql(request.question)
        return {"question": request.question, "sql": sql}
    except SQLCannotAnswerError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SQLGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ModelRequestError as exc:
        # In a public API, replace detailed errors with a generic message.
        raise HTTPException(status_code=503, detail="Local LLM unavailable") from exc
