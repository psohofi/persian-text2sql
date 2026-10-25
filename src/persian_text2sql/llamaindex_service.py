"""LlamaIndex -> local Ollama -> SQLGlot (no database execution)."""

from pathlib import Path
from typing import Optional, Union

from .base import BaseSQLService
from .exceptions import ModelRequestError


class LlamaIndexSQLService(BaseSQLService):
    def __init__(
        self,
        schema_path: Optional[Union[str, Path]] = None,
        schema: Optional[str] = None,
        model: str = "gemma4:12b",
        host: str = "http://localhost:11434",
        dialect: str = "MariaDB",
        temperature: float = 0.0,
        num_ctx: int = 8192,
        timeout: float = 900.0,
        num_predict: int = 1024,
        max_retries: int = 1,
        debug: bool = False,
    ) -> None:
        super().__init__(
            schema_path=schema_path, schema=schema, dialect=dialect,
            max_retries=max_retries, debug=debug,
        )
        try:
            from llama_index.llms.ollama import Ollama
        except ImportError as exc:
            raise ImportError(
                'LlamaIndex backend missing. Install: pip install -e ".[llamaindex]"'
            ) from exc
        # In recent LlamaIndex Ollama, `additional_kwargs` are passed to Ollama's
        # options, including num_predict. Adjust if using an older integration.
        self.llm = Ollama(
            model=model,
            base_url=host,
            temperature=temperature,
            context_window=num_ctx,
            request_timeout=timeout,
            additional_kwargs={"num_predict": num_predict},
        )

    def _ask_sync(self, prompt: str) -> str:
        try:
            response = self.llm.complete(prompt)
            return response.text or ""
        except Exception as exc:
            raise ModelRequestError(
                f"LlamaIndex/Ollama request failed: {exc}. "
                "Check Ollama, model, timeout, RAM/VRAM and schema size."
            ) from exc

    async def _ask_async(self, prompt: str) -> str:
        try:
            response = await self.llm.acomplete(prompt)
            return response.text or ""
        except Exception as exc:
            raise ModelRequestError(
                f"LlamaIndex/Ollama request failed: {exc}. "
                "Check Ollama, model, timeout, RAM/VRAM and schema size."
            ) from exc

    def generate_sql_sync(self, question: str, schema: Optional[str] = None) -> str:
        return self._generate_sync(question, schema, self._ask_sync)

    async def generate_sql(self, question: str, schema: Optional[str] = None) -> str:
        """Uses native async Ollama completions via LlamaIndex."""
        return await self._generate_async(question, schema, self._ask_async)
