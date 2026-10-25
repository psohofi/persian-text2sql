"""Vanna 2.0.2 -> local Ollama -> SQLGlot.

This intentionally uses Vanna's LLM service, not its agent or DB execution tools.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Union

from .base import BaseSQLService
from .exceptions import ModelRequestError


class VannaSQLService(BaseSQLService):
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
            from vanna.core.llm import LlmMessage, LlmRequest
            from vanna.core.user import User
            from vanna.integrations.ollama import OllamaLlmService
        except ImportError as exc:
            raise ImportError(
                'Vanna backend missing. Install: pip install -e ".[vanna]"'
            ) from exc
        self._LlmMessage = LlmMessage
        self._LlmRequest = LlmRequest
        self._user = User(id="local-sql-user", group_memberships=["user"])
        self.llm = OllamaLlmService(
            model=model, host=host, temperature=temperature,
            num_ctx=num_ctx, timeout=timeout, num_predict=num_predict,
        )
        self.temperature = temperature

    def _ask_blocking(self, prompt: str) -> str:
        request = self._LlmRequest(
            user=self._user,
            system_prompt=(
                "You are a SQL generator. Follow the user prompt; "
                "return SQL only or CANNOT_ANSWER."
            ),
            messages=[self._LlmMessage(role="user", content=prompt)],
            tools=None,
            temperature=self.temperature,
        )
        try:
            # Vanna 2.0.2 OllamaLlmService.send_request is declared async,
            # but calls Ollama's synchronous client internally.
            response = asyncio.run(self.llm.send_request(request))
            return response.content or ""
        except Exception as exc:
            raise ModelRequestError(
                f"Vanna/Ollama request failed: {exc}. "
                "Check Ollama, model, timeout, RAM/VRAM and schema size."
            ) from exc

    def generate_sql_sync(self, question: str, schema: Optional[str] = None) -> str:
        """Blocking API. Prefer `await generate_sql()` inside async servers.

        A notebook or async caller may already have an event loop running.
        In that case, run Vanna's asyncio.run() call in a separate thread.
        This still blocks the caller, so use the async API in async servers.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return self._generate_sync(question, schema, self._ask_blocking)
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(
                self._generate_sync, question, schema, self._ask_blocking
            ).result()

    async def generate_sql(self, question: str, schema: Optional[str] = None) -> str:
        """Runs blocking Vanna Ollama adapter in a worker thread."""
        return await asyncio.to_thread(self.generate_sql_sync, question, schema)
