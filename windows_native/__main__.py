from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ConfigStore
from .diagnostics import export_diagnostics
from .hardware import detect_hardware, recommended_models
from .models import ModelRegistry
from .migrations import SQLiteMigrationRunner
from .paths import resolve_paths


def _json_default(value):
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dict__"):
        return value.__dict__
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m windows_native", description="Odysseus Windows-native maintenance CLI")
    parser.add_argument("--app-dir", type=Path, default=None, help="Application directory used to resolve portable mode")
    parser.add_argument("--portable", action="store_true", help="Use app-dir/data instead of LOCALAPPDATA")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create the Windows-native data directory structure and default config")
    sub.add_parser("hardware", help="Print detected hardware and model recommendations as JSON")
    sub.add_parser("list-models", help="List managed local GGUF models as JSON")
    diag = sub.add_parser("export-diagnostics", help="Create a redacted diagnostics ZIP")
    diag.add_argument("--output", type=Path, default=None, help="Destination ZIP path")

    args = parser.parse_args(argv)
    paths = resolve_paths(args.app_dir, portable=True if args.portable else None).ensure()

    if args.command == "init":
        store = ConfigStore(paths)
        config = store.load()
        store.save(config)
        applied = SQLiteMigrationRunner(paths.database / "app.db").apply()
        print(json.dumps({"root": str(paths.root), "config": str(store.path), "portable": paths.portable, "migrations_applied": [m.version for m in applied]}, indent=2))
        return 0

    if args.command == "hardware":
        info = detect_hardware()
        print(json.dumps({"hardware": info, "recommended_models": recommended_models(info)}, default=_json_default, indent=2))
        return 0

    if args.command == "list-models":
        registry = ModelRegistry(paths.models)
        print(json.dumps([model.to_dict() for model in registry.list_models()], indent=2))
        return 0

    if args.command == "export-diagnostics":
        archive = export_diagnostics(paths, args.output)
        print(json.dumps({"diagnostics": str(archive)}, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
