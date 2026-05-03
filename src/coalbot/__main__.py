from __future__ import annotations

import argparse
from pathlib import Path

from coalbot.bot import run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="coalbot",
        description="Delete Discord messages once they receive enough coal reactions.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Path to the JSON config file. Defaults to ./config.json.",
    )
    args = parser.parse_args()

    run(args.config)


if __name__ == "__main__":
    main()
