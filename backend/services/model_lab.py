"""Read the latest precomputed public model evaluation report."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from backend.errors import ApiError


class ModelLabService:
    def __init__(self, artifact_root: Path | str = "artifacts/cross_sectional"):
        self.artifact_root = Path(artifact_root)
        self._report: dict[str, Any] | None = None
        self._mtime: float | None = None
        self._lock = Lock()

    @property
    def available(self) -> bool:
        try:
            manifest = json.loads((self.artifact_root / "latest.json").read_text())
            return (self.artifact_root / manifest["model_version"] / "model_lab.json").is_file()
        except (FileNotFoundError, KeyError, ValueError):
            return False

    def get_report(self) -> dict[str, Any]:
        try:
            manifest = json.loads((self.artifact_root / "latest.json").read_text())
            report_path = self.artifact_root / manifest["model_version"] / "model_lab.json"
        except (FileNotFoundError, KeyError, ValueError) as error:
            raise ApiError("Model Lab is unavailable until the first production evaluation is published.", 503, "model_lab_unavailable") from error
        if not report_path.is_file():
            raise ApiError("Model Lab is unavailable until the first production evaluation is published.", 503, "model_lab_unavailable")
        modified = report_path.stat().st_mtime
        if self._report is not None and self._mtime == modified:
            return self._report
        with self._lock:
            self._report = json.loads(report_path.read_text())
            self._mtime = modified
            return self._report
