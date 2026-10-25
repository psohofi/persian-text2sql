"""Exceptions exposed by both SQL-generation backends."""


class SQLGenerationError(ValueError):
    """Model output did not produce an acceptable SQL query."""


class SQLCannotAnswerError(SQLGenerationError):
    """Model says the question cannot be answered from the schema."""


class ModelRequestError(RuntimeError):
    """Could not get a response from the local Ollama model."""
