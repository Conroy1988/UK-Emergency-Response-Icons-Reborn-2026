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

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT, SCALE = 32, 37, 4
STATES = {
    "red": "#ff4d5a",
    "yellow": "#ffc857",
    "green": "#3bd672",
}
LEVEL_COLOURS = {1: "#5ee27a", 2: "#42c6ff", 3: "#ffd166", 4: "#ff8c42", 5: "#ff416c"}
SERVICE_COLOURS = {
    "fire": "#ff5a47",
    "police": "#4ca6ff",
    "ambulance": "#29d391",
    "marine": "#22c7d9",
    "mountain": "#b88cff",
    "air": "#ffcf5a",
    "rail": "#e067ff",
    "hazmat": "#c6ef4e",
    "mixed": "#f1f5f9",
}

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
    ("eod", re.compile(r"bomb|eod|explosive|ordnance|munition|suspicious package|firework", re.I)),
    ("aircraft", re.compile(r"aircraft|airfield|airport|helicopter|runway|bird strike|plane", re.I)),
    ("rail", re.compile(r"train|rail|tram|subway|locomotive|platform", re.I)),
    ("marine", re.compile(r"boat|ship|vessel|sea |coast|drown|canoe|kayak|water rescue|lifeboat|offshore|harbour|river", re.I)),
    ("mountain", re.compile(r"mountain|hiker|hike|fell running|cliff|ravine|cave|mineshaft|abseil|moorland", re.I)),
    ("collapse", re.compile(r"collapse|cave-in|landslide|sinkhole", re.I)),
    ("collision", re.compile(r"collision|\brtc\b|road accident|crash|rollover|vehicle.*(hit|accident)|hit and run|car into|cyclist hit", re.I)),
    ("fire", re.compile(r"fire|burning|blaze|smoke|ignited|flashover|bonfire", re.I)),
    ("cardiac", re.compile(r"cardiac|heart|chest pain|respiratory arrest|anaphylaxis|unconscious", re.I)),
    ("medical", re.compile(r"pain|injur|seizure|asthma|bleed|haemorrhage|fever|allergic|medical|patient|fall|fallen|birth|intoxication|electrocution|choking|burns", re.I)),
    ("weather", re.compile(r"flood|storm|snow|ice|wind|weather|lightning", re.I)),
    ("animal", re.compile(r"animal|dog|cat|horse|swan|bird|livestock|deer|rabbit", re.I)),
    ("crowd", re.compile(r"protest|demonstration|crowd|brawl|fight|party|rave|disorder|riot", re.I)),
    ("crime", re.compile(r"theft|robbery|burglary|stolen|shoplifting|assault|weapon|warrant|intruder|bail|crime|domestic violence|missing person|kidnap", re.I)),
    ("utilities", re.compile(r"power line|electric|substation|water main|utility|telegraph pole", re.I)),
    ("rescue", re.compile(r"rescue|trapped|stuck|stranded|concern for welfare|search", re.I)),
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


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"), Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf")):
        if path.exists(): return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def line(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], fill: str, width: int = 2) -> None:
    draw.line([(x*SCALE, y*SCALE) for x, y in points], fill=fill, width=width*SCALE, joint="curve")


def pictogram(draw: ImageDraw.ImageDraw, family: str, colour: str) -> None:
    w, white, accent = SCALE, "#f8fafc", colour
    if family == "fire":
        draw.polygon([(14*w,28*w),(9*w,24*w),(10*w,18*w),(15*w,11*w),(15*w,18*w),(20*w,14*w),(21*w,22*w),(18*w,28*w)], fill=accent)
        draw.polygon([(15*w,26*w),(12*w,23*w),(15*w,18*w),(18*w,23*w)], fill=white)
    elif family in {"police", "crime"}:
        draw.rounded_rectangle((9*w,12*w,21*w,27*w), radius=3*w, outline=accent, width=2*w)
        draw.polygon([(15*w,15*w),(17*w,20*w),(21*w,20*w),(18*w,22*w),(19*w,26*w),(15*w,24*w),(11*w,26*w),(12*w,22*w),(9*w,20*w),(13*w,20*w)], fill=white)
    elif family in {"medical", "cardiac"}:
        if family == "cardiac":
            draw.polygon([(15*w,27*w),(9*w,20*w),(10*w,15*w),(15*w,16*w),(18*w,13*w),(22*w,16*w),(21*w,21*w)], fill=accent)
            line(draw, [(10,21),(13,21),(14,18),(16,24),(18,20),(21,20)], white, 1)
        else:
            draw.rounded_rectangle((9*w,13*w,21*w,27*w), radius=3*w, outline=accent, width=2*w)
            draw.rectangle((13*w,16*w,17*w,24*w), fill=white); draw.rectangle((11*w,18*w,19*w,22*w), fill=white)
    elif family == "collision":
        draw.rounded_rectangle((8*w,18*w,15*w,24*w), radius=1*w, outline=white, width=2*w)
        draw.rounded_rectangle((18*w,16*w,24*w,23*w), radius=1*w, outline=accent, width=2*w)
        line(draw, [(14,17),(16,19),(18,16)], "#ffd166", 1)
        draw.ellipse((9*w,23*w,12*w,26*w), fill=white); draw.ellipse((20*w,22*w,23*w,25*w), fill=accent)
    elif family == "aircraft":
        draw.polygon([(15*w,10*w),(18*w,19*w),(24*w,22*w),(24*w,24*w),(17*w,23*w),(17*w,28*w),(20*w,30*w),(20*w,31*w),(15*w,30*w),(10*w,31*w),(10*w,30*w),(13*w,28*w),(13*w,23*w),(7*w,24*w),(7*w,22*w),(13*w,19*w)], fill=accent)
    elif family == "rail":
        draw.rounded_rectangle((9*w,11*w,21*w,26*w), radius=2*w, outline=accent, width=2*w)
        draw.rectangle((11*w,14*w,19*w,18*w), fill=white); draw.ellipse((11*w,22*w,14*w,25*w), fill=white); draw.ellipse((17*w,22*w,20*w,25*w), fill=white)
        line(draw, [(11,28),(14,25),(17,25),(20,28)], white, 1)
    elif family == "marine":
        draw.polygon([(8*w,21*w),(23*w,21*w),(20*w,26*w),(11*w,26*w)], fill=accent)
        draw.rectangle((14*w,15*w,18*w,21*w), fill=white); draw.polygon([(18*w,15*w),(22*w,19*w),(18*w,19*w)], fill=white)
        line(draw, [(7,28),(11,27),(15,28),(19,27),(23,28)], white, 1)
    elif family == "mountain":
        draw.polygon([(7*w,27*w),(14*w,12*w),(19*w,21*w),(22*w,16*w),(25*w,27*w)], fill=accent)
        draw.polygon([(12*w,17*w),(14*w,12*w),(17*w,18*w),(15*w,17*w),(14*w,20*w)], fill=white)
    elif family == "hazmat":
        draw.ellipse((9*w,13*w,21*w,25*w), outline=accent, width=2*w)
        for a in (0,120,240):
            import math as _m
            cx,cy=15*w,19*w; rad=_m.radians(a)
            x=cx+int(_m.cos(rad)*5*w); y=cy+int(_m.sin(rad)*5*w)
            draw.ellipse((x-2*w,y-2*w,x+2*w,y+2*w), fill=white)
        draw.ellipse((13*w,17*w,17*w,21*w), fill=accent)
    elif family == "eod":
        draw.ellipse((10*w,15*w,21*w,27*w), fill=accent)
        line(draw, [(15,15),(18,11),(21,12)], white, 1); draw.ellipse((20*w,10*w,23*w,13*w), fill="#ffd166")
    elif family == "collapse":
        draw.polygon([(8*w,15*w),(14*w,11*w),(14*w,27*w),(8*w,27*w)], fill=accent)
        draw.polygon([(16*w,12*w),(23*w,15*w),(23*w,27*w),(17*w,27*w)], fill=white)
        line(draw, [(15,13),(17,17),(14,20),(17,24),(15,28)], "#ff8c42", 1)
    elif family == "weather":
        draw.ellipse((8*w,17*w,18*w,25*w), fill=white); draw.ellipse((14*w,14*w,24*w,25*w), fill=accent); draw.rectangle((9*w,20*w,23*w,25*w), fill=accent)
        line(draw, [(11,28),(10,31)], "#42c6ff", 1); line(draw, [(17,28),(16,31)], "#42c6ff", 1); line(draw, [(22,28),(21,31)], "#42c6ff", 1)
    elif family == "animal":
        draw.ellipse((10*w,18*w,21*w,28*w), fill=accent)
        for x,y in ((10,15),(15,13),(20,15),(23,19)):
            draw.ellipse(((x-2)*w,(y-2)*w,(x+2)*w,(y+2)*w), fill=white)
    elif family == "crowd":
        for x,y,c in ((10,17,white),(16,14,accent),(22,17,white)):
            draw.ellipse(((x-2)*w,(y-2)*w,(x+2)*w,(y+2)*w), fill=c)
            draw.rounded_rectangle(((x-3)*w,(y+2)*w,(x+3)*w,(y+10)*w), radius=2*w, fill=c)
    elif family == "utilities":
        draw.polygon([(17*w,10*w),(10*w,22*w),(15*w,22*w),(12*w,31*w),(22*w,18*w),(17*w,18*w)], fill="#ffd166")
    elif family == "rescue":
        draw.ellipse((13*w,11*w,18*w,16*w), fill=white); line(draw, [(15,16),(15,24),(10,28)], white, 2); line(draw, [(15,20),(21,17)], accent, 2); line(draw, [(15,24),(21,29)], accent, 2)
        draw.ellipse((8*w,26*w,12*w,30*w), outline=accent, width=1*w)
    else:
        draw.rounded_rectangle((9*w,13*w,21*w,27*w), radius=4*w, outline=accent, width=2*w)
        draw.rectangle((13*w,16*w,17*w,24*w), fill=white); draw.rectangle((11*w,18*w,19*w,22*w), fill=white)


def render_icon(state: str, level: int, service: str, family: str) -> Image.Image:
    image = Image.new("RGBA", (WIDTH*SCALE, HEIGHT*SCALE), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    status, accent, level_colour = STATES[state], SERVICE_COLOURS[service], LEVEL_COLOURS[level]
    # high-contrast pin body and tail
    draw.rounded_rectangle((1*SCALE,1*SCALE,31*SCALE,33*SCALE), radius=5*SCALE, fill="#111b27", outline="#e7eef799", width=1*SCALE)
    draw.polygon([(13*SCALE,32*SCALE),(19*SCALE,32*SCALE),(16*SCALE,36*SCALE)], fill=status)
    draw.rounded_rectangle((3*SCALE,5*SCALE,5*SCALE,29*SCALE), radius=SCALE, fill=accent)
    draw.ellipse((7*SCALE,5*SCALE,12*SCALE,10*SCALE), fill=status, outline="#0b111a", width=SCALE)
    pictogram(draw, family, accent)
    draw.ellipse((20*SCALE,2*SCALE,31*SCALE,13*SCALE), fill="#081018", outline=level_colour, width=2*SCALE)
    fnt = font(8*SCALE)
    box = draw.textbbox((0,0), str(level), font=fnt)
    tw, th = box[2]-box[0], box[3]-box[1]
    draw.text((25.5*SCALE-tw/2,7.2*SCALE-th/2-box[1]), str(level), font=fnt, fill="#ffffff")
    draw.rounded_rectangle((5*SCALE,30*SCALE,27*SCALE,33*SCALE), radius=SCALE, fill=status)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


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
        entry={
            "mission_id":sid,"slot_id":slot_id,"name":record["name"],
            "categories":record.get("mission_categories",[]),**classification,
        }
        manifest_records.append(entry); groups[slot_id].append(entry)

    legacy_payload=json.loads((root/"data"/"legacy-slots.json").read_text(encoding="utf-8"))
    legacy={slot["slot_id"]:slot for slot in legacy_payload["slots"]}
    active_slot_count=len(groups)
    numeric_slots=[str(value) for value in range(864)]
    missing=sorted(set(numeric_slots)-set(groups),key=int)
    if missing!=sorted(legacy,key=int):
        raise SystemExit(f"Legacy slot index does not exactly cover inactive MissionChief slots: {missing}")

    slot_specs=[
        {"slot_id":"handoff","name":"Hand-off Mission","source_kind":"special","mission_ids":[],"variant_count":0,"level":2,"score":0.0,"components":{},"primary_service":"mixed","services":["mixed"],"family":"response","categories":[]},
        {"slot_id":"alliance_custom","name":"Custom Alliance Mission","source_kind":"special","mission_ids":[],"variant_count":0,"level":3,"score":0.0,"components":{},"primary_service":"mixed","services":["mixed"],"family":"response","categories":[]},
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
                "family":canonical["family"],"categories":sorted({category for member in members for category in member["categories"]}),
            })
        else:
            retained=legacy[slot_id]
            synthetic={"name":retained["name"],"requirements":{},"additional":{},"chances":{},"mission_categories":[]}
            classification=classify(synthetic)
            slot_specs.append({
                "slot_id":slot_id,"name":retained["name"],"source_kind":"legacy","mission_ids":[],"variant_count":0,
                "level":retained["level"],"score":classification["score"],"components":classification["components"],
                "max_level_source_mission_id":None,"primary_service":classification["primary_service"],"services":classification["services"],
                "family":classification["family"],"categories":[],
            })

    manifest_slots=[]
    for index, slot in enumerate(slot_specs, 1):
        filename=f"{index:04d}--{safe_id(slot['slot_id'])}--{slugify(slot['name'])}.png"
        files={}
        for state in STATES:
            path=output_root/state/filename
            icon=render_icon(state, slot["level"], slot["primary_service"], slot["family"])
            icon.save(path, optimize=True)
            files[state]=path.relative_to(root).as_posix()
        manifest_slots.append({"order":index,**slot,"files":files})

    generated = {
        "schema_version":1,
        "project":"UK Emergency Response Icons Reborn 2026",
        "catalogue_record_count":len(records),
        "official_slot_count":len(numeric_slots),
        "active_slot_count":active_slot_count,
        "legacy_slot_count":len(legacy),
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
        "schema_version":1,"thresholds":{"1":"score < 4.2","2":"4.2 <= score < 10","3":"10 <= score < 21","4":"21 <= score < 50","5":"score >= 50"},
        "slot_level_distribution":dict(sorted(Counter(str(r["level"]) for r in manifest_slots).items())),
        "record_level_distribution":dict(sorted(Counter(str(r["level"]) for r in manifest_records).items())),
        "family_distribution":dict(sorted(Counter(r["family"] for r in manifest_slots).items())),
        "service_distribution":dict(sorted(Counter(r["primary_service"] for r in manifest_slots).items())),
    }
    (root/"data"/"classifier-profile.json").write_text(json.dumps(profile,indent=2)+"\n",encoding="utf-8")
    with (root/"data"/"mission-manifest.csv").open("w",newline="",encoding="utf-8") as fh:
        writer=csv.writer(fh); writer.writerow(["order","slot_id","name","variant_count","mission_ids","level","score","primary_service","family","red","yellow","green"])
        for r in manifest_slots: writer.writerow([r["order"],r["slot_id"],r["name"],r["variant_count"]," ".join(r["mission_ids"]),r["level"],r["score"],r["primary_service"],r["family"],r["files"]["red"],r["files"]["yellow"],r["files"]["green"]])
    print(f"Mapped {len(records)} official records to {len(numeric_slots)} native slots and rendered {len(manifest_slots)*3} images")


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--source",type=Path,default=Path("data/source/missionchief-uk.json")); parser.add_argument("--root",type=Path,default=Path(".")); args=parser.parse_args()
    build(args.source,args.root.resolve())


if __name__=="__main__": main()
