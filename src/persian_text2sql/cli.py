"""CLI entry point: persian-text2sql --backend llamaindex --schema ... QUESTION"""

import argparse
import logging
import sys

from .exceptions import SQLGenerationError, ModelRequestError


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate MariaDB SQL from a Persian question using local Ollama."
    )
    parser.add_argument("question", nargs="*", help="Persian question; prompted if omitted")
    parser.add_argument("--backend", choices=("vanna", "llamaindex"), default="llamaindex")
    parser.add_argument("--schema", default="examples/schema.md", help="UTF-8 .md/.sql/.txt schema")
    parser.add_argument("--model", default="gemma4:12b")
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--num-predict", type=int, default=1024)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.WARNING)
    question = " ".join(args.question).strip() or input("Persian question: ").strip()

    if args.backend == "vanna":
        from .vanna_service import VannaSQLService as Service
    else:
        from .llamaindex_service import LlamaIndexSQLService as Service

    try:
        service = Service(
            schema_path=args.schema, model=args.model, host=args.host,
            timeout=args.timeout, num_ctx=args.num_ctx,
            num_predict=args.num_predict, max_retries=args.max_retries,
            debug=args.debug,
        )
        print(service.generate_sql_sync(question))
    except (ValueError, SQLGenerationError, ModelRequestError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
