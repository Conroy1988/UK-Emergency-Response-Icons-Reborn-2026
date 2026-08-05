#!/usr/bin/env python3
"""Validate coverage, pixels, state separation and small-map visibility."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STATES=("red","yellow","green")
EXPECTED={(255,77,90),(255,200,87),(59,214,114)}
BACKGROUNDS=((232,237,242),(23,32,43),(81,97,75),(117,123,128))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixels(image: Image.Image):
    getter=getattr(image,"get_flattened_data",None)
    return getter() if getter is not None else image.getdata()


def validate(root: Path) -> dict:
    manifest=json.loads((root/"data"/"mission-manifest.json").read_text(encoding="utf-8"))
    records=manifest["records"]; slots=manifest["slots"]; checks=[]; errors=[]
    def check(name: str, passed: bool, detail: str="") -> None:
        checks.append({"name":name,"passed":bool(passed),"detail":detail})
        if not passed: errors.append(f"{name}: {detail}")

    ids=[r["mission_id"] for r in records]
    active_slots=[r for r in slots if r["source_kind"]=="official"]
    legacy_slots=[r for r in slots if r["source_kind"]=="legacy"]
    official_slots=[r for r in slots if r["source_kind"] in {"official","legacy"}]
    special_slots=[r for r in slots if r["source_kind"]=="special"]
    slot_ids=[r["slot_id"] for r in slots]
    check("catalogue_record_count",len(records)==manifest["catalogue_record_count"],str(len(records)))
    check("unique_mission_ids",len(ids)==len(set(ids)),str(len(set(ids))))
    check("official_slot_count",len(official_slots)==manifest["official_slot_count"]==864,str(len(official_slots)))
    check("active_slot_count",len(active_slots)==manifest["active_slot_count"],str(len(active_slots)))
    check("legacy_slot_count",len(legacy_slots)==manifest["legacy_slot_count"]==37,str(len(legacy_slots)))
    check("special_slot_count",len(special_slots)==manifest["special_slot_count"]==2,str(len(special_slots)))
    check("contiguous_official_slots",[r["slot_id"] for r in official_slots]==[str(i) for i in range(864)],"")
    check("unique_upload_slots",len(slot_ids)==len(set(slot_ids))==manifest["upload_slot_count"],str(len(slot_ids)))
    mapped_ids=[mission_id for slot in active_slots for mission_id in slot["mission_ids"]]
    check("every_record_mapped_once",sorted(mapped_ids)==sorted(ids),f"{len(mapped_ids)} mappings")
    check("all_levels_present",set(r["level"] for r in slots)=={1,2,3,4,5},str(Counter(r["level"] for r in slots)))
    check("all_states_declared",set(manifest["states"])==set(STATES),str(manifest["states"]))

    seen_paths=set(); pixel_fail=[]; state_fail=[]; visibility_fail=[]; hashes=[]
    for record in slots:
        images=[]
        for state in STATES:
            path=root/record["files"][state]
            if not path.exists(): pixel_fail.append(f"missing:{path}"); continue
            seen_paths.add(path); hashes.append(sha(path))
            with Image.open(path) as im:
                if im.size!=(32,37) or im.mode!="RGBA": pixel_fail.append(f"shape:{path}:{im.size}:{im.mode}")
                alpha=im.getchannel("A")
                bbox=alpha.getbbox(); coverage=sum(1 for p in pixels(alpha) if p>16)/(32*37)
                if bbox is None or not (0.35 <= coverage <= 0.9): pixel_fail.append(f"coverage:{path}:{coverage:.3f}")
                if alpha.getpixel((0,0))>8 or alpha.getpixel((31,0))>8: pixel_fail.append(f"corner:{path}")
                images.append(im.convert("RGBA").copy())
        if len(images)==3:
            base=list(pixels(images[0])); other=list(pixels(images[1])); third=list(pixels(images[2]))
            d12=sum(a!=b for a,b in zip(base,other)); d13=sum(a!=b for a,b in zip(base,third))
            if not (20 <= d12 <= 300 and 20 <= d13 <= 300): state_fail.append(f"{record['slot_id']}:{d12}:{d13}")
            # The marker silhouette and average contrast must survive at 50% map scale.
            test=images[0].resize((16,19),Image.Resampling.LANCZOS)
            mask=test.getchannel("A")
            visible=sum(1 for p in pixels(mask) if p>48)
            if visible < 125:
                visibility_fail.append(f"pixels:{record['slot_id']}:{visible}")
            for bg in BACKGROUNDS:
                canvas=Image.new("RGBA",test.size,(*bg,255)); canvas.alpha_composite(test)
                differences=[]
                for out_px,alpha_px in zip(pixels(canvas.convert("RGB")),pixels(mask)):
                    if alpha_px>48: differences.append(sum(abs(out_px[i]-bg[i]) for i in range(3))/3)
                contrast=sum(differences)/len(differences) if differences else 0
                if contrast < 34:
                    visibility_fail.append(f"contrast:{record['slot_id']}:{bg}:{contrast:.1f}")
    check("three_files_per_slot",len(seen_paths)==len(slots)*3,f"{len(seen_paths)} files")
    check("png_integrity",not pixel_fail,"; ".join(pixel_fail[:10]))
    check("state_separation",not state_fail,"; ".join(state_fail[:10]))
    check("half_scale_map_visibility",not visibility_fail,"; ".join(visibility_fail[:10]))
    check("unique_render_hashes",len(set(hashes))>=len(slots)*0.10,f"{len(set(hashes))} distinct renders")

    report={
        "schema_version":1,"all_passed":not errors,"catalogue_record_count":len(records),"official_slot_count":len(official_slots),
        "active_slot_count":len(active_slots),"legacy_slot_count":len(legacy_slots),
        "special_slot_count":len(special_slots),"upload_slot_count":len(slots),"image_count":len(seen_paths),
        "level_distribution":dict(sorted(Counter(str(r["level"]) for r in slots).items())),
        "family_distribution":dict(sorted(Counter(r["family"] for r in slots).items())),
        "checks":checks,"errors":errors,
    }
    (root/"data"/"qa-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if errors: raise SystemExit("\n".join(errors))
    print(json.dumps(report,indent=2))
    return report


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=Path(".")); args=parser.parse_args(); validate(args.root.resolve())


if __name__=="__main__": main()
