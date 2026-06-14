#!/usr/bin/env python3
"""Bulk-update one validation field across a filtered set of template YAML files.

Reference:
    Stage 6 Phase 1 Completion Brief v6.2 and Stage 6 Phase D1 Brief v6.3.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


VALIDATION_FIELDS = frozenset({"verifier_certified", "pi_validated", "v2_validated"})
TRUE_VALUES = {"1", "true", "yes", "y"}
FALSE_VALUES = {"0", "false", "no", "n"}


def parse_bool(raw_value: str) -> bool:
    """Parse a CLI boolean string.

    Args:
        raw_value: User-provided truthy or falsy token.

    Returns:
        Parsed boolean value.
    """

    lowered = raw_value.strip().lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got {raw_value!r}.")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the validation-field updater."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-filter", required=True, help="Template-id prefix to update.")
    parser.add_argument(
        "--field",
        required=True,
        choices=sorted(VALIDATION_FIELDS),
        help="Validation field under the YAML `validation` section.",
    )
    parser.add_argument("--value", required=True, type=parse_bool, help="Boolean value to write.")
    parser.add_argument(
        "--template-dir",
        default="data/raw/templates",
        help="Directory containing template YAML files.",
    )
    return parser.parse_args()


def update_validation_field(
    *,
    template_dir: Path,
    template_filter: str,
    field_name: str,
    field_value: bool,
) -> int:
    """Update one validation field across all matching templates.

    Args:
        template_dir: Directory containing template YAML files.
        template_filter: Prefix filter applied to YAML stem names.
        field_name: Validation field to update.
        field_value: Boolean value to assign.

    Returns:
        Number of files updated.
    """

    matching_paths = sorted(path for path in template_dir.glob("*.yaml") if path.stem.startswith(template_filter))
    if not matching_paths:
        raise FileNotFoundError(
            f"No template YAML files under {template_dir} match prefix {template_filter!r}."
        )

    for path in matching_paths:
        payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
        validation = payload.setdefault("validation", {})
        validation[field_name] = field_value
        path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return len(matching_paths)


def main() -> None:
    """Apply the requested validation update and report the file count."""

    args = parse_args()
    updated_count = update_validation_field(
        template_dir=Path(args.template_dir),
        template_filter=args.template_filter,
        field_name=args.field,
        field_value=args.value,
    )
    print(f"Updated {updated_count} template(s).")


if __name__ == "__main__":
    main()
