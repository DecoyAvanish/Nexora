import json

from backend.services.model_lab import ModelLabService


def test_model_lab_reads_latest_versioned_report(tmp_path):
    root = tmp_path / "cross_sectional"
    version = root / "2026.11.17"
    version.mkdir(parents=True)
    (root / "latest.json").write_text(json.dumps({"model_version": "2026.11.17"}))
    expected = {"model_version": "2026.11.17", "walk_forward": {"mean_auc": 0.53}}
    (version / "model_lab.json").write_text(json.dumps(expected))
    service = ModelLabService(root)
    assert service.available is True
    assert service.get_report() == expected
