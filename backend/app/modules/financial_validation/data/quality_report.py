"""Persist dataset quality summaries (no ML dependency)."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_quality_report(report: dict[str, Any], output_dir: str | Path) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out / f"quality_{stamp}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provisional": True,
        **report,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
