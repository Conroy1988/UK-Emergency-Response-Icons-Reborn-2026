#!/usr/bin/env python3
"""Build the deterministic public release archive."""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"
VERSION=(os.environ.get("PACK_VERSION") or os.environ.get("GITHUB_REF_NAME") or "v1.0.1").removeprefix("v")
NAME=f"UK-Emergency-Response-Icons-Reborn-2026-v{VERSION}.zip"


def main() -> None:
    report=json.loads((ROOT/"data"/"qa-report.json").read_text())
    if not report.get("all_passed"): raise SystemExit("QA report is not green")
    DIST.mkdir(exist_ok=True); target=DIST/NAME
    include=[ROOT/"assets"/"icons",ROOT/"assets"/"previews",ROOT/"data"/"mission-manifest.json",ROOT/"data"/"mission-manifest.csv",ROOT/"data"/"classifier-profile.json",ROOT/"data"/"legacy-slots.json",ROOT/"data"/"provisional-slots.json",ROOT/"data"/"qa-report.json",ROOT/"docs"/"CLASSIFICATION.md",ROOT/"docs"/"STYLE_GUIDE.md",ROOT/"README.md",ROOT/"LICENSE.md"]
    files=[]
    for item in include:
        files.extend(sorted(p for p in item.rglob("*") if p.is_file())) if item.is_dir() else files.append(item)
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(set(files)):
            info=zipfile.ZipInfo(path.relative_to(ROOT).as_posix(),date_time=(2026,8,5,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o644<<16
            z.writestr(info,path.read_bytes())
    digest=hashlib.sha256(target.read_bytes()).hexdigest(); (DIST/(NAME+".sha256")).write_text(f"{digest}  {NAME}\n")
    print(f"{target} {digest}")


if __name__=="__main__": main()
