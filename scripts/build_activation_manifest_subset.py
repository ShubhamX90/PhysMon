#!/usr/bin/env python3
"""Build a combined activation manifest over a selected family subset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from physmon.utils.io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-manifests",
        nargs="+",
        required=True,
        help="One or more manifest.json files whose entries should be combined.",
    )
    parser.add_argument(
        "--family-ids",
        nargs="*",
        default=(),
        help="Optional explicit family ids to keep.",
    )
    parser.add_argument(
        "--family-prefixes",
        nargs="*",
        default=(),
        help="Optional family-id prefixes to keep, e.g. CM_C_.",
    )
    parser.add_argument(
        "--site",
        default=None,
        help="Optional site filter, e.g. resid_post_last_prompt.",
    )
    parser.add_argument(
        "--output-manifest",
        required=True,
        help="Output manifest.json path.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def keep_entry(
    entry: dict[str, Any],
    *,
    family_ids: set[str],
    family_prefixes: tuple[str, ...],
    site: str | None,
) -> bool:
    template_id = str(entry["template_id"])
    if site is not None and str(entry.get("site")) != site:
        return False
    if family_ids and template_id in family_ids:
        return True
    if family_prefixes and any(template_id.startswith(prefix) for prefix in family_prefixes):
        return True
    return not family_ids and not family_prefixes


def main() -> None:
    args = parse_args()
    family_ids = set(str(item) for item in args.family_ids)
    family_prefixes = tuple(str(item) for item in args.family_prefixes)

    files: list[dict[str, Any]] = []
    seen = set()
    for manifest_path in [Path(path) for path in args.input_manifests]:
        manifest = load_manifest(manifest_path)
        for entry in manifest.get("files", []):
            if not keep_entry(
                entry,
                family_ids=family_ids,
                family_prefixes=family_prefixes,
                site=args.site,
            ):
                continue
            key = (
                str(entry["template_id"]),
                int(entry["variant_id"]),
                str(entry["site"]),
                str(entry["tensor_path"]),
            )
            if key in seen:
                continue
            seen.add(key)
            files.append(entry)

    files.sort(key=lambda item: (str(item["template_id"]), int(item["variant_id"]), str(item["site"])))
    payload = {
        "source_manifests": [str(Path(path).resolve()) for path in args.input_manifests],
        "site_filter": args.site,
        "family_ids": sorted(family_ids),
        "family_prefixes": list(family_prefixes),
        "n_files": len(files),
        "files": files,
    }
    output_path = Path(args.output_manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)


if __name__ == "__main__":
    main()
