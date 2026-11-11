"""G0 item (d): every tagged comparator is tagged, sourced, and matches its stored value."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TAGS = ROOT / "docs" / "registry" / "v2" / "comparator_tags.yml"


def _lookup(payload, dotted: str):
    for part in dotted.split("."):
        payload = payload[part]
    return payload


def _entries():
    return yaml.safe_load(TAGS.read_text(encoding="utf-8"))["comparators"]


def test_every_comparator_has_a_valid_tag_and_reason():
    entries = _entries()
    assert len({e["id"] for e in entries}) == len(entries)
    for entry in entries:
        assert entry["tag"] in ("oracle", "deployable"), entry["id"]
        assert entry.get("role", "comparator") in ("comparator", "subject", "diagnostic"), entry["id"]
        assert entry["reason"].strip() and entry["access"].strip(), entry["id"]


def test_stated_values_match_the_source_artifacts():
    for entry in _entries():
        source = ROOT / entry["artifact"]
        assert source.is_file(), entry["artifact"]
        stored = _lookup(json.loads(source.read_text(encoding="utf-8")), entry["field"])
        assert round(float(stored), 4) == round(float(entry["value"]), 4), entry["id"]


def test_the_wave2_comparator_and_the_paper_entropy_baseline_are_oracle():
    tags = {e["id"]: e["tag"] for e in _entries()}
    assert tags["wave2_combined_non_activation"] == "oracle"
    assert tags["entropy_fitted_logprob"] == "oracle"
    assert tags["token_entropy_std"] == "deployable"
