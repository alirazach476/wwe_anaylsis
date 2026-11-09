"""Phase 3 validation smoke tests."""

from pathlib import Path

from wwe_data.validation.dataset_checks import run_dataset_checks


def test_dataset_checks_against_exports():
    exports = Path("data/exports")
    if not (exports / "matches.csv").exists():
        return
    report = run_dataset_checks(exports)
    assert report.summary["matches"] > 0
    assert report.ok, [c.detail for c in report.failed]
