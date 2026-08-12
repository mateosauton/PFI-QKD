#!/usr/bin/env python3
"""Run the local guided QKD study application."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local QKD study app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--state-root", type=Path, default=ROOT / ".study_state")
    args = parser.parse_args()

    from study_app.server import create_server

    server = create_server(args.host, args.port, args.state_root)
    print(f"QKD study app: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nQKD study app detenido.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
