"""The ICLR 2027 review-claims audit must keep reproducing from the committed data."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "reviews" / "check_iclr2027_review_claims.py"


def test_claims_check_reproduces_and_has_no_unevaluated_or_different_checks(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--out-dir", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True, env={"PYTHONNOUSERSITE": "1", "PATH": "/usr/bin:/bin"},
        check=False, timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-800:]
    results = json.loads((tmp_path / "claims_check.json").read_text(encoding="utf-8"))
    verdicts = {r["id"]: r["verdict"] for r in results}
    bad = {k: v for k, v in verdicts.items() if v in ("DIFFERENT", "NOT_EVALUATED")}
    assert not bad, bad
    assert sum(v == "CONFIRMED" for v in verdicts.values()) >= 20
    assert (tmp_path / "claims_check.md").read_text(encoding="utf-8").startswith("# ICLR 2027 review claims")


def test_committed_audit_output_matches_a_fresh_run(tmp_path):
    subprocess.run([sys.executable, str(SCRIPT), "--out-dir", str(tmp_path)], cwd=ROOT, check=True,
                   capture_output=True, env={"PYTHONNOUSERSITE": "1", "PATH": "/usr/bin:/bin"}, timeout=300)
    fresh = json.loads((tmp_path / "claims_check.json").read_text(encoding="utf-8"))
    committed = json.loads((ROOT / "results/reviews/iclr2027_submission50608/attempt_20261111/claims_check.json")
                           .read_text(encoding="utf-8"))
    assert fresh == committed
