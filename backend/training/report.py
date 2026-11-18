"""Print a deployment-friendly summary of the latest model artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/cross_sectional"))
    args = parser.parse_args()
    manifest = json.loads((args.artifacts / "latest.json").read_text())
    print(f"Model version: {manifest['model_version']}")
    print(f"Data through: {manifest['data_through']}")
    print(f"Universe: {manifest['universe']}")
    print(f"Features: {manifest['feature_count']}")
    print(f"Walk-forward folds: {manifest['fold_count']}")
    print(f"Model AUC: {manifest['mean_model_auc']:.4f}")
    print(f"Momentum baseline AUC: {manifest['mean_momentum_auc']:.4f}")
    print(f"Information coefficient: {manifest['mean_information_coefficient']:.4f}")


if __name__ == "__main__":
    main()
