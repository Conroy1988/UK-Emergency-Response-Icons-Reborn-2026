#!/usr/bin/env python3
"""Classify MissionChief missions and render the complete three-state icon pack."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from icon_style_v2 import HEIGHT, LEVEL_COLOURS, STATES, WIDTH, render_icon, signature_for

SEVERE_TERMS = re.compile(
    r"major|mass casualty|catastroph|nuclear|cbrne|aircraft (?:crash|accident)|"
    r"train derail|passenger train fire|bridge collapse|building collapse|explosion|"
    r"terror|firearms attack|chemical|chlorine|ammonia|munitions|power station",
    re.I,
)
MODERATE_TERMS = re.compile(
    r"persons reported|entrap|trapped|serious|large|industrial|hazmat|rescue|"
    r"collision|rtc|weapon|missing|flood|tunnel|high rise|hospital|school|care home",
    re.I,
)

FAMILY_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("hazmat", re.compile(r"nuclear|cbrne|chemical|chlorine|ammonia|gas leak|hazard|poison|fuel spill|tanker spill|carbon monoxide", re.I)),
    ("eod", re.compile(r"bomb|grenade|eod|explosive|ordnance|munition|suspicious package|firework", re.I)),
    ("aircraft", re.compile(r"\b(?:aircraft|airfield|airport|helicopter|runway|plane)\b|bird strike", re.I)),
    ("rail", re.compile(r"\b(?:train|tram|subway|locomotive)\b|\brail(?:way)?\b", re.I)),
    ("marine", re.compile(r"\b(?:boat|ship|vessel|sea|coast|canoe|kayak|lifeboat|river)\b|drown|water rescue|offshore|harbour", re.I)),
    ("mountain", re.compile(r"mountain|hiker|hike|fell running|cliff|ravine|cave|mineshaft|abseil|moorland", re.I)),
    ("collapse", re.compile(r"collapse|cave-in|landslide|sinkhole", re.I)),
    ("collision", re.compile(r"collid|collision|\brtc\b|road accident|crash|rollover|overturn|vehicle.*(hit|accident)|hit and run|hit by|struck by|\bstruck\b|car into|cyclist hit", re.I)),
    ("fire", re.compile(r"fire|burning|blaze|smoke|ignited|flashover|bonfire", re.I)),
    ("weather", re.compile(r"flood|storm|snow|ice|wind|weather|lightning", re.I)),
    ("utilities", re.compile(r"power line|powerline|electric|substation|water main|utility|telegraph pole|solar panel|gutter|roof tile|pipeline|hydrant", re.I)),
    ("animal", re.compile(r"\b(?:animal|dog|cat|horse|swan|bird|livestock|deer|rabbit|cow|sheep|goat|snake)\b", re.I)),
    ("crowd", re.compile(r"protest|demonstration|crowd|brawl|fight|party|rave|disorder|riot|awareness|celebration|ceremony|announcement", re.I)),
    ("crime", re.compile(r"theft|robbery|burglary|stolen|shoplifting|assault|weapon|warrant|intruder|bail|crime|domestic violence|missing person|kidnap", re.I)),
    ("police", re.compile(r"fare dodger|traffic stop|speed enforcement|speed detection|abandoned car|broken down car|obstructing road|\banpr\b|noise complaint|statement gathering", re.I)),
    ("rescue", re.compile(r"rescue|trapped|stuck|stranded|concern for welfare|search|falling|at risk of falling", re.I)),
    ("cardiac", re.compile(r"cardiac|heart|chest pain|respiratory arrest|\bcpr\b", re.I)),
    ("medical", re.compile(r"pain|injur|seizure|asthma|bleed|haemorrhage|fever|allergic|anaphyla|unconscious|medical|mental health|admission|patient|fall|fallen|birth|intoxication|electrocution|choking|burns", re.I)),
]

SPECIALIST_TOKENS = (
    "command", "hazmat", "foam", "aerial", "platform", "rescue", "drone", "dog",
    "helicopter", "coastal", "boat", "eod", "hart", "mass_casualty", "railway",
    "airfield", "traffic", "tow", "water_tanker", "officer", "chief", "welfare",
)
HEAVY_TOKENS = ("helicopter", "aircraft", "large_coastal", "major_foam", "eod", "mass_casualty", "railway_fire")


def flatten_numbers(value: Any, prefix: str = "") -> Iterable[tuple[str, float]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flatten_numbers(child, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, (int, float)) and not isinstance(value, bool) and not prefix.endswith("min_pump_speed"):
        yield prefix, float(value)


def service_for(record: dict[str, Any]) -> tuple[str, list[str]]:
    haystack = " ".join(record.get("mission_categories", [])) + " " + str(record.get("additional", {}).get("filter_id", ""))
    req = " ".join(record.get("requirements", {}).keys())
    services: set[str] = set()
    if re.search(r"fire|firehouse", haystack, re.I) or re.search(r"firetruck|battalion|hazmat|platform|foam", req, re.I): services.add("fire")
    if re.search(r"police", haystack, re.I) or re.search(r"police|traffic|armed|cell|prison", req, re.I): services.add("police")
    if re.search(r"ambulance|rescue_station|medical", haystack, re.I) or record.get("additional", {}).get("possible_patient"): services.add("ambulance")
    if re.search(r"coastal|ocean", haystack + " " + req, re.I): services.add("marine")
    if re.search(r"mountain", haystack + " " + req, re.I): services.add("mountain")
    if re.search(r"airfield|airport", haystack + " " + req, re.I): services.add("air")
    if re.search(r"railway", haystack + " " + req, re.I): services.add("rail")
    if re.search(r"hazmat|chemical|foam", haystack + " " + req, re.I): services.add("hazmat")
    if not services: services.add("mixed")
    ordered = sorted(services)
    filter_id = str(record.get("additional", {}).get("filter_id", ""))
    if "coastal" in filter_id: primary = "marine"
    elif "mountain" in filter_id: primary = "mountain"
    elif "airport" in filter_id or "airfield" in filter_id: primary = "air"
    elif "ambulance" in filter_id: primary = "ambulance"
    elif "police" in filter_id: primary = "police"
    elif "firehouse" in filter_id: primary = "fire"
    elif len(ordered) == 1: primary = ordered[0]
    else: primary = "mixed"
    return primary, ordered


def family_for(record: dict[str, Any], primary: str) -> str:
    name = record.get("name", "")
    for family, pattern in FAMILY_RULES:
        if pattern.search(name):
            return family
    return {"fire": "fire", "police": "police", "ambulance": "medical", "marine": "marine", "mountain": "mountain", "air": "aircraft", "rail": "rail", "hazmat": "hazmat"}.get(primary, "response")


def classify(record: dict[str, Any]) -> dict[str, Any]:
    req_items = list(flatten_numbers(record.get("requirements", {})))
    resource_score = 0.0
    specialist_count = 0
    for key, quantity in req_items:
        weight = 1.0
        if any(token in key for token in SPECIALIST_TOKENS):
            weight = 1.65
            specialist_count += int(math.ceil(quantity))
        if any(token in key for token in HEAVY_TOKENS):
            weight = 2.35
        if "personnel_educations" in key:
            weight = 0.45
        resource_score += max(0.0, quantity) * weight

    primary, services = service_for(record)
    patient_max = float(record.get("additional", {}).get("possible_patient") or 0)
    patient_min = float(record.get("additional", {}).get("possible_patient_min") or 0)
    transport = float(record.get("chances", {}).get("patient_transport") or 0) / 100
    critical = float(record.get("chances", {}).get("patient_critical_care") or 0) / 100
    patient_score = min(13.0, patient_max * 0.28 + patient_min * 0.12 + patient_max * transport * 0.08 + patient_max * critical * 0.14)
    codes = set(record.get("additional", {}).get("patient_uk_code_possible") or [])
    if "C-1" in codes: clinical_score = 11.0
    elif "C-2" in codes: clinical_score = 4.5
    elif "C-3" in codes: clinical_score = 2.0
    elif "C-4" in codes: clinical_score = 0.5
    else: clinical_score = 0.0
    if re.search(r"patient transfer|interfacility transfer", str(record.get("name", "")), re.I):
        clinical_score = min(clinical_score, 4.0)
    service_score = max(0, len([s for s in services if s not in {"hazmat", "rail", "air"}]) - 1) * 2.4
    credits = float(record.get("average_credits") or 0)
    credit_score = min(7.0, math.sqrt(max(0.0, credits)) / 18.0)
    name = str(record.get("name", ""))
    hazard_score = 0.0
    if MODERATE_TERMS.search(name): hazard_score += 2.0
    if SEVERE_TERMS.search(name): hazard_score += 5.0
    additional = record.get("additional", {})
    if additional.get("only_alliance_mission") or additional.get("unavailable_in_normal_missions"): hazard_score += 4.0
    if specialist_count >= 3: hazard_score += min(4.0, specialist_count * 0.22)

    score = round(resource_score + patient_score + clinical_score + service_score + credit_score + hazard_score, 2)
    if score < 4.2: level = 1
    elif score < 10.0: level = 2
    elif score < 21.0: level = 3
    elif score < 50.0: level = 4
    else: level = 5
    return {
        "level": level,
        "score": score,
        "components": {
            "resources": round(resource_score, 2),
            "patients": round(patient_score, 2),
            "clinical_acuity": round(clinical_score, 2),
            "services": round(service_score, 2),
            "credits": round(credit_score, 2),
            "hazards": round(hazard_score, 2),
        },
        "primary_service": primary,
        "services": services,
        "family": family_for(record, primary),
    }


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:72] or "mission"


def safe_id(value: str) -> str:
    return value.replace("/", "-").replace(".", "-")


def build(source: Path, root: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    records = payload["records"]
    output_root = root / "assets" / "icons"
    for state in STATES:
        state_root=output_root/state
        state_root.mkdir(parents=True, exist_ok=True)
        for old_file in state_root.glob("*.png"):
            old_file.unlink()

    manifest_records=[]
    groups=defaultdict(list)
    for record in records:
        classification=classify(record); sid=str(record["id"]); slot_id=str(record.get("base_mission_id"))
        signature=signature_for(str(record.get("name", "")), classification["family"])
        entry={
            "mission_id":sid,"slot_id":slot_id,"name":record["name"],
            "categories":record.get("mission_categories",[]),**classification,**signature,
        }
        manifest_records.append(entry); groups[slot_id].append(entry)

    legacy_payload=json.loads((root/"data"/"legacy-slots.json").read_text(encoding="utf-8"))
    legacy={slot["slot_id"]:slot for slot in legacy_payload["slots"]}
    provisional_payload=json.loads((root/"data"/"provisional-slots.json").read_text(encoding="utf-8"))
    provisional={slot["slot_id"]:slot for slot in provisional_payload["slots"]}
    active_slot_count=len(groups)
    numeric_ids=[int(value) for value in groups if value.isdigit()]
    declared_ids=[int(value) for value in provisional if value.isdigit()]
    numeric_slot_count=max(numeric_ids+declared_ids)+1
    numeric_slots=[str(value) for value in range(numeric_slot_count)]
    missing=sorted(set(numeric_slots)-set(groups),key=int)
    uncovered=sorted(set(missing)-set(legacy)-set(provisional),key=int)
    if uncovered:
        raise SystemExit(f"Inactive MissionChief slots are not declared as legacy or provisional: {uncovered}")

    slot_specs=[
        {"slot_id":"handoff","name":"Hand-off Mission","source_kind":"special","mission_ids":[],"variant_count":0,"level":2,"score":0.0,"components":{},"primary_service":"mixed","services":["mixed"],"family":"response","modifier":"response","subject":"response","signature":"response:response:response","categories":[]},
        {"slot_id":"alliance_custom","name":"Custom Alliance Mission","source_kind":"special","mission_ids":[],"variant_count":0,"level":3,"score":0.0,"components":{},"primary_service":"mixed","services":["mixed"],"family":"response","modifier":"response","subject":"response","signature":"response:response:response","categories":[]},
    ]
    for slot_id in numeric_slots:
        members=groups[slot_id]
        if members:
            canonical=next((member for member in members if member["mission_id"]==slot_id),members[0])
            maximum=max(members,key=lambda member:(member["level"],member["score"]))
            slot_specs.append({
                "slot_id":slot_id,"name":canonical["name"],"source_kind":"official","mission_ids":[member["mission_id"] for member in members],
                "variant_count":len(members),"level":maximum["level"],"score":maximum["score"],"components":maximum["components"],
                "max_level_source_mission_id":maximum["mission_id"],"primary_service":canonical["primary_service"],"services":canonical["services"],
                "family":canonical["family"],"modifier":canonical["modifier"],"subject":canonical["subject"],"signature":canonical["signature"],
                "categories":sorted({category for member in members for category in member["categories"]}),
            })
        elif slot_id in provisional:
            retained=provisional[slot_id]
            retained_signature=signature_for(retained["name"], retained["family"])
            slot_specs.append({
                "slot_id":slot_id,"name":retained["name"],"source_kind":"provisional","mission_ids":[],"variant_count":0,
                "level":retained["level"],"score":0.0,"components":{},"max_level_source_mission_id":None,
                "primary_service":retained["primary_service"],"services":retained["services"],"family":retained["family"],
                **retained_signature,"categories":retained.get("categories",[]),"provisional_rationale":retained["rationale"],
            })
        else:
            retained=legacy[slot_id]
            synthetic={"name":retained["name"],"requirements":{},"additional":{},"chances":{},"mission_categories":[]}
            classification=classify(synthetic)
            retained_signature=signature_for(retained["name"], classification["family"])
            slot_specs.append({
                "slot_id":slot_id,"name":retained["name"],"source_kind":"legacy","mission_ids":[],"variant_count":0,
                "level":retained["level"],"score":classification["score"],"components":classification["components"],
                "max_level_source_mission_id":None,"primary_service":classification["primary_service"],"services":classification["services"],
                "family":classification["family"],**retained_signature,"categories":[],
            })

    manifest_slots=[]
    for index, slot in enumerate(slot_specs, 1):
        filename=f"{index:04d}--{safe_id(slot['slot_id'])}--{slugify(slot['name'])}.png"
        files={}
        for state in STATES:
            path=output_root/state/filename
            icon=render_icon(
                state,
                slot["level"],
                slot["primary_service"],
                slot["services"],
                slot["family"],
                slot["modifier"],
                slot["subject"],
            )
            icon.save(path, optimize=True)
            files[state]=path.relative_to(root).as_posix()
        manifest_slots.append({"order":index,**slot,"files":files})

    generated = {
        "schema_version":2,
        "project":"UK Emergency Response Icons Reborn 2026",
        "style_version":"2.0",
        "style_features":["mission_signature","multi_service_rail","shape_coded_state","optical_level_shield"],
        "catalogue_record_count":len(records),
        "official_slot_count":len(numeric_slots),
        "active_slot_count":active_slot_count,
        "legacy_slot_count":len(legacy),
        "provisional_slot_count":sum(slot["source_kind"]=="provisional" for slot in manifest_slots),
        "published_official_slot_count":sum(slot["source_kind"] in {"official","legacy"} for slot in manifest_slots),
        "special_slot_count":2,
        "upload_slot_count":len(manifest_slots),
        "catalogue_sha256":payload["source_sha256"],
        "canvas":{"width":WIDTH,"height":HEIGHT},
        "states":STATES,
        "levels":{str(k):v for k,v in LEVEL_COLOURS.items()},
        "records":manifest_records,
        "slots":manifest_slots,
    }
    (root/"data").mkdir(exist_ok=True)
    (root/"data"/"mission-manifest.json").write_text(json.dumps(generated,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    profile={
        "schema_version":2,"style_version":"2.0","thresholds":{"1":"score < 4.2","2":"4.2 <= score < 10","3":"10 <= score < 21","4":"21 <= score < 50","5":"score >= 50"},
        "slot_level_distribution":dict(sorted(Counter(str(r["level"]) for r in manifest_slots).items())),
        "record_level_distribution":dict(sorted(Counter(str(r["level"]) for r in manifest_records).items())),
        "family_distribution":dict(sorted(Counter(r["family"] for r in manifest_slots).items())),
        "modifier_distribution":dict(sorted(Counter(r["modifier"] for r in manifest_slots).items())),
        "subject_distribution":dict(sorted(Counter(r["subject"] for r in manifest_slots).items())),
        "signature_distribution":dict(sorted(Counter(r["signature"] for r in manifest_slots).items())),
        "distinct_signature_count":len(set(r["signature"] for r in manifest_slots)),
        "service_distribution":dict(sorted(Counter(r["primary_service"] for r in manifest_slots).items())),
    }
    (root/"data"/"classifier-profile.json").write_text(json.dumps(profile,indent=2)+"\n",encoding="utf-8")
    with (root/"data"/"mission-manifest.csv").open("w",newline="",encoding="utf-8") as fh:
        writer=csv.writer(fh,lineterminator="\n"); writer.writerow(["order","slot_id","name","variant_count","mission_ids","level","score","primary_service","family","modifier","subject","signature","red","yellow","green"])
        for r in manifest_slots: writer.writerow([r["order"],r["slot_id"],r["name"],r["variant_count"]," ".join(r["mission_ids"]),r["level"],r["score"],r["primary_service"],r["family"],r["modifier"],r["subject"],r["signature"],r["files"]["red"],r["files"]["yellow"],r["files"]["green"]])
    print(f"Mapped {len(records)} official records to {len(numeric_slots)} native slots and rendered {len(manifest_slots)*3} images")


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--source",type=Path,default=Path("data/source/missionchief-uk.json")); parser.add_argument("--root",type=Path,default=Path(".")); args=parser.parse_args()
    build(args.source,args.root.resolve())


if __name__=="__main__": main()
