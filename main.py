"""Flow2API - Main Entry Point"""

import os

from src.main import app
import uvicorn


__all__ = ["app", "resolve_server_port"]


def resolve_server_port(config_port: int) -> int:
    """Resolve runtime port, preferring Zeabur-style PORT when valid."""
    raw_port = os.environ.get("PORT", "").strip()
    if not raw_port:
        return config_port
    try:
        return int(raw_port)
    except ValueError:
        return config_port


if __name__ == "__main__":
    from src.core.config import config

    uvicorn.run(
        "src.main:app",
        host=config.server_host,
        port=resolve_server_port(config.server_port),
        reload=False,
    )
