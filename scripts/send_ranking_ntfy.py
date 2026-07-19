#!/usr/bin/env python3
"""Send ranking-cron status through the existing private ntfy topic."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    import tomli as tomllib
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SERVER = "https://ntfy.sh"
CONFIG_PATHS = [
    REPO_ROOT / ".streamlit/secrets.toml",
    Path("/home/albertovth/GitHub/copa_america2024/.streamlit/secrets.toml"),
]
LEVELS = {
    "success": ("default", "white_check_mark"),
    "info": ("low", "information_source"),
    "warning": ("high", "warning"),
    "error": ("urgent", "rotating_light"),
}


def read_config() -> tuple[str, str, str]:
    values: dict[str, object] = {}
    for path in CONFIG_PATHS:
        if path.exists():
            with path.open("rb") as stream:
                values.update(tomllib.load(stream))
            break
    topic = str(os.environ.get("NTFY_TOPIC") or values.get("NTFY_TOPIC") or "")
    server = str(
        os.environ.get("NTFY_SERVER") or values.get("NTFY_SERVER") or DEFAULT_SERVER
    )
    click = str(os.environ.get("NTFY_CLICK") or values.get("NTFY_CLICK") or "")
    return topic, server, click


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", choices=LEVELS, default="info")
    parser.add_argument("--title", default="Football ranking cron")
    parser.add_argument("--message", default="")
    parser.add_argument("--check-config", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    topic, server, click = read_config()
    if not topic:
        print("ntfy is not configured", file=sys.stderr)
        return 2
    if args.check_config:
        print("ntfy topic is configured")
        return 0
    priority, tags = LEVELS[args.level]
    headers = {
        "Title": args.title,
        "Priority": priority,
        "Tags": tags,
        "Content-Type": "text/plain; charset=utf-8",
    }
    if click:
        headers["Click"] = click
    request = Request(
        f"{server.rstrip('/')}/{quote(topic, safe='')}",
        data=args.message.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            if not 200 <= response.status < 300:
                print(f"ntfy returned HTTP {response.status}", file=sys.stderr)
                return 1
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"ntfy send failed: {type(error).__name__}", file=sys.stderr)
        return 1
    print(f"ntfy {args.level} notification sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
