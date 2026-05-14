from __future__ import annotations

import sys

from clfc.cli.parser import build_parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    return int(args.handler(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
