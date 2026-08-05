#!/usr/bin/env python3
"""Fetch or import the live MissionChief UK mission catalogue deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = "https://www.missionchief.co.uk/einsaetze.json"


def load_payload(path: Path | None) -> bytes:
    if path is not None:
        return path.read_bytes()
    request = Request(SOURCE_URL, headers={"User-Agent": "TKB-UK-Incident-Status/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Use a previously downloaded JSON array")
    parser.add_argument("--output", type=Path, default=Path("data/source/missionchief-uk.json"))
    args = parser.parse_args()

    payload = load_payload(args.input)
    records = json.loads(payload)
    if not isinstance(records, list) or not records:
        raise SystemExit("MissionChief catalogue must be a non-empty JSON array")

    ids = [str(record.get("id", "")) for record in records]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise SystemExit("Mission IDs must be present and unique")

    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        if existing.get("source_sha256") == digest:
            print(f"Catalogue unchanged at {len(records)} missions")
            return

    result = {
        "schema_version": 1,
        "source_url": SOURCE_URL,
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_sha256": digest,
        "count": len(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} missions to {args.output}")


if __name__ == "__main__":
    main()
