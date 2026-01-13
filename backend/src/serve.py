"""CLI entry point — run with `uv run mcp-home`."""

import uvicorn

from app import create_app


def main() -> None:
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
