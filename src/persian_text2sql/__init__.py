"""Persian-to-MariaDB SQL with a choice of LLM frameworks.

Import backends lazily so installing one does not require installing both.
"""

from .exceptions import SQLGenerationError, SQLCannotAnswerError, ModelRequestError

__all__ = [
    "VannaSQLService", "LlamaIndexSQLService", "SQLGenerationError",
    "SQLCannotAnswerError", "ModelRequestError",
]


def __getattr__(name: str):
    if name == "VannaSQLService":
        from .vanna_service import VannaSQLService
        return VannaSQLService
    if name == "LlamaIndexSQLService":
        from .llamaindex_service import LlamaIndexSQLService
        return LlamaIndexSQLService
    raise AttributeError(name)
