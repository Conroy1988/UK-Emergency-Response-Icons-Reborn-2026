#!/usr/bin/env python3
"""Validate V4 coverage, premium scene detail and small-map visibility."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STATES=("red","yellow","green")
BACKGROUNDS=((232,237,242),(23,32,43),(81,97,75),(117,123,128))
EXPECTED_SIZE=(64,83)


def state_signal(image: Image.Image, state: str) -> int:
    """Count strongly state-coded visible pixels without requiring flat fills."""
    count=0
    for red,green,blue,alpha in pixels(image.convert("RGBA")):
        if alpha < 100: continue
        if state=="red" and red>155 and red>green*1.45 and red>blue*1.15: count+=1
        elif state=="yellow" and red>145 and green>80 and blue<105 and red>green*1.15: count+=1
        elif state=="green" and green>125 and green>red*1.25 and green>blue*1.12: count+=1
    return count


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
    provisional_slots=[r for r in slots if r["source_kind"]=="provisional"]
    official_slots=[r for r in slots if r["source_kind"] in {"official","legacy","provisional"}]
    published_slots=[r for r in slots if r["source_kind"] in {"official","legacy"}]
    special_slots=[r for r in slots if r["source_kind"]=="special"]
    slot_ids=[r["slot_id"] for r in slots]
    check("catalogue_record_count",len(records)==manifest["catalogue_record_count"],str(len(records)))
    check("unique_mission_ids",len(ids)==len(set(ids)),str(len(set(ids))))
    check("official_slot_count",len(official_slots)==manifest["official_slot_count"],str(len(official_slots)))
    check("published_official_slot_count",len(published_slots)==manifest["published_official_slot_count"],str(len(published_slots)))
    check("active_slot_count",len(active_slots)==manifest["active_slot_count"],str(len(active_slots)))
    check("legacy_slot_count",len(legacy_slots)==manifest["legacy_slot_count"]==37,str(len(legacy_slots)))
    check("provisional_slot_count",len(provisional_slots)==manifest["provisional_slot_count"],str(len(provisional_slots)))
    check("special_slot_count",len(special_slots)==manifest["special_slot_count"]==2,str(len(special_slots)))
    check("contiguous_official_slots",[r["slot_id"] for r in official_slots]==[str(i) for i in range(manifest["official_slot_count"])],"")
    check("unique_upload_slots",len(slot_ids)==len(set(slot_ids))==manifest["upload_slot_count"],str(len(slot_ids)))
    mapped_ids=[mission_id for slot in active_slots for mission_id in slot["mission_ids"]]
    check("every_record_mapped_once",sorted(mapped_ids)==sorted(ids),f"{len(mapped_ids)} mappings")
    check("all_levels_present",set(r["level"] for r in slots)=={1,2,3,4,5},str(Counter(r["level"] for r in slots)))
    check("all_states_declared",set(manifest["states"])==set(STATES),str(manifest["states"]))
    check("operational_v4_style",manifest.get("schema_version")==4 and manifest.get("style_version")=="4.0",f"schema {manifest.get('schema_version')} · style {manifest.get('style_version')}")
    required_features={"premium_illustrated_scene_masters","semantic_scene_mapping","multi_service_lightbar","state_choreography","integrated_response_shield","native_row_identity_code"}
    declared_features=set(manifest.get("style_features",[]))
    check("operational_v4_features",required_features.issubset(declared_features),str(sorted(declared_features)))
    signatures=[r.get("signature") for r in slots]
    check("mission_signature_coverage",all(signatures),f"{sum(bool(value) for value in signatures)} signatures")
    check("semantic_signature_depth",len(set(signatures))>=200,f"{len(set(signatures))} distinct semantic compositions")
    chassis=[r.get("chassis") for r in slots]
    scene_codes=[r.get("scene_code") for r in slots]
    check("family_chassis_coverage",all(chassis) and len(set(chassis))>=10,f"{sum(bool(value) for value in chassis)} slots · {len(set(chassis))} chassis")
    check("incident_scene_code_coverage",all(scene_codes) and len(set(scene_codes))==len(slots),f"{sum(bool(value) for value in scene_codes)} slots · {len(set(scene_codes))} distinct codes")
    boundary_rules={
        "bus":re.compile(r"\b(?:bus|buses|coach|coaches)\b",re.I),
        "hgv":re.compile(r"\b(?:hgv|truck|lorry|tanker|tractor|trailer|harvester)\b",re.I),
        "animal":re.compile(r"\b(?:animal|dog|cat|horse|swan|bird|livestock|deer|rabbit|cow|sheep|goat|snake|reindeer|stable|stables)\b",re.I),
        "rail":re.compile(r"\b(?:train|tram|locomotive)\b|\brail(?:way)?\b",re.I),
        "retail":re.compile(r"shopping centre|\b(?:supermarket|shop|market|store|bakery|restaurant|pub|nightclub)\b",re.I),
        "water":re.compile(r"\b(?:water|sea|beach|river|harbour|offshore)\b|coast(?:line)?|drown|swim|flood",re.I),
    }
    boundary_fail=[f"{slot['slot_id']}:{slot['name']}:{slot['subject']}" for slot in slots for token,pattern in boundary_rules.items() if slot.get("subject")==token and not pattern.search(slot["name"])]
    check("semantic_token_boundaries",not boundary_fail,"; ".join(boundary_fail[:10]))
    eod_fail=[f"{slot['slot_id']}:{slot['name']}:{slot['family']}" for slot in slots if re.search(r"unexploded|\b(?:bomb|grenade|ordnance)\b",slot["name"],re.I) and slot["family"]!="eod"]
    check("eod_signature_routing",not eod_fail,"; ".join(eod_fail[:10]))

    scene_root=root/"assets"/"scenes"
    scene_files=list(scene_root.glob("*.png"))
    expected_scenes={re.sub(r"[^a-z0-9]+","--",signature.lower()).strip("-")+".png" for signature in signatures}
    check("premium_scene_master_count",len(scene_files)==len(expected_scenes)==264,f"{len(scene_files)} files · {len(expected_scenes)} expected")
    check("premium_scene_master_coverage",{path.name for path in scene_files}==expected_scenes,f"{len({path.name for path in scene_files}&expected_scenes)}/{len(expected_scenes)} signatures")

    seen_paths=set(); pixel_fail=[]; state_fail=[]; visibility_fail=[]; hashes=[]; red_hashes=[]; complexities=[]
    for record in slots:
        images=[]
        for state in STATES:
            path=root/record["files"][state]
            if not path.exists(): pixel_fail.append(f"missing:{path}"); continue
            seen_paths.add(path); hashes.append(sha(path))
            if state=="red": red_hashes.append(sha(path))
            with Image.open(path) as im:
                if im.size!=EXPECTED_SIZE or im.mode!="RGBA": pixel_fail.append(f"shape:{path}:{im.size}:{im.mode}")
                alpha=im.getchannel("A")
                bbox=alpha.getbbox(); opaque=sum(1 for p in pixels(alpha) if p>32)
                if bbox is None or not (900 <= opaque <= 4700): pixel_fail.append(f"coverage:{path}:{opaque}")
                corners=(alpha.getpixel((0,0)),alpha.getpixel((63,0)),alpha.getpixel((0,82)),alpha.getpixel((63,82)))
                if corners!=(0,0,0,0): pixel_fail.append(f"corners:{path}:{corners}")
                complexity=len(im.getcolors(maxcolors=100_000) or [])
                complexities.append(complexity)
                if complexity < 180: pixel_fail.append(f"scene-complexity:{path}:{complexity}")
                signal=state_signal(im,state)
                if signal < 18: pixel_fail.append(f"state-colour:{path}:{signal}")
                images.append(im.convert("RGBA").copy())
        if len(images)==3:
            base=list(pixels(images[0])); other=list(pixels(images[1])); third=list(pixels(images[2]))
            d12=sum(a!=b for a,b in zip(base,other)); d13=sum(a!=b for a,b in zip(base,third))
            if not (900 <= d12 <= 3000 and 900 <= d13 <= 3000): state_fail.append(f"{record['slot_id']}:{d12}:{d13}")
            # The marker silhouette and average contrast must survive at 50% map scale.
            test=images[0].resize((32,42),Image.Resampling.LANCZOS)
            mask=test.getchannel("A")
            visible=sum(1 for p in pixels(mask) if p>48)
            if visible < 450:
                visibility_fail.append(f"pixels:{record['slot_id']}:{visible}")
            for bg in BACKGROUNDS:
                canvas=Image.new("RGBA",test.size,(*bg,255)); canvas.alpha_composite(test)
                differences=[]
                for out_px,alpha_px in zip(pixels(canvas.convert("RGB")),pixels(mask)):
                    if alpha_px>48: differences.append(sum(abs(out_px[i]-bg[i]) for i in range(3))/3)
                contrast=sum(differences)/len(differences) if differences else 0
                strong_fraction=(sum(value>=40 for value in differences)/len(differences)) if differences else 0
                if contrast < 27 or strong_fraction < 0.20:
                    visibility_fail.append(f"contrast:{record['slot_id']}:{bg}:{contrast:.1f}:{strong_fraction:.3f}")
    check("three_files_per_slot",len(seen_paths)==len(slots)*3,f"{len(seen_paths)} files")
    check("png_integrity",not pixel_fail,"; ".join(pixel_fail[:10]))
    check("state_separation",not state_fail,"; ".join(state_fail[:10]))
    check("half_scale_map_visibility",not visibility_fail,"; ".join(visibility_fail[:10]))
    check("unique_render_hashes",len(set(hashes))==len(hashes),f"{len(set(hashes))} distinct renders")
    check("mission_aware_red_renders",len(set(red_hashes))==len(slots),f"{len(set(red_hashes))} distinct red-state renders")
    check("premium_scene_colour_depth",min(complexities,default=0)>=180,f"minimum {min(complexities,default=0)} colours")

    report={
        "schema_version":4,"style_version":manifest.get("style_version"),"all_passed":not errors,"catalogue_record_count":len(records),"official_slot_count":len(official_slots),
        "active_slot_count":len(active_slots),"legacy_slot_count":len(legacy_slots),
        "provisional_slot_count":len(provisional_slots),"published_official_slot_count":len(published_slots),
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
