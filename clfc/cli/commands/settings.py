from __future__ import annotations

import json
import sys
from argparse import Namespace

from clfc.core.settings import load_settings, set_default, settings_path


def run(args: Namespace) -> int:
    if args.settings_command == "show":
        payload = load_settings()
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0
        print(f"Settings: {settings_path()}")
        defaults = payload["defaults"]
        for key in sorted(defaults):
            print(f"  {key}: {defaults[key]}")
        return 0

    if args.settings_command == "set":
        try:
            payload = set_default(args.key, args.value)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            normalized = args.key.replace("-", "_")
            print(f"Updated {normalized}: {payload['defaults'].get(normalized)}")
            if normalized == "dangerously_skip_permissions" and payload["defaults"].get(normalized):
                print("WARNING: future `clfc interactive` launches will bypass Claude Code permission checks.")
        return 0

    print("Expected a settings subcommand.", file=sys.stderr)
    return 2
