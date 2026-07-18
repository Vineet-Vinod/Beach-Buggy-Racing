#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from formula_assets.manifest import discover_manifests
from formula_assets.pipeline import build, preview_saved, validate_saved


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Blender sources and GLB runtime assets")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list registered asset manifests")

    for command, help_text in (
        ("build", "generate .blend, .glb, metadata, and preview"),
        ("validate", "validate existing .blend and .glb files"),
        ("preview", "render a preview from an existing .blend file"),
    ):
        subparser = subparsers.add_parser(command, help=help_text)
        subparser.add_argument("asset", help="asset id or 'all'")
    return parser.parse_args()


def select_assets(manifests, requested: str):
    if requested == "all":
        return manifests.values()
    if requested not in manifests:
        choices = ", ".join(manifests)
        raise ValueError(f"unknown asset '{requested}'; available: {choices}")
    return (manifests[requested],)


def main() -> int:
    args = parse_args()
    try:
        manifests = discover_manifests(ROOT)
        if args.command == "list":
            for asset_id, manifest in manifests.items():
                generator = "yes" if asset_id in __import__("formula_assets.generators", fromlist=["GENERATORS"]).GENERATORS else "no"
                print(f"{asset_id:24} {manifest.kind:12} generator={generator}")
            return 0

        for manifest in select_assets(manifests, args.asset):
            if args.command == "build":
                report = build(manifest)
                print(json.dumps(report, indent=2))
            elif args.command == "validate":
                print(json.dumps(validate_saved(manifest), indent=2))
            elif args.command == "preview":
                preview_saved(manifest)
                print(manifest.preview.relative_to(ROOT))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"asset pipeline error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

