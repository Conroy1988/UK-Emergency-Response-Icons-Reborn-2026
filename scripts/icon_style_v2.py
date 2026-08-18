#!/usr/bin/env python3
"""Operational V2 rendering grammar for the MissionChief UK icon pack."""

from __future__ import annotations

import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT, SCALE = 32, 37, 8

STATES = {
    "red": "#ff4357",
    "yellow": "#ffc145",
    "green": "#32d583",
}

LEVEL_COLOURS = {
    1: "#5ee27a",
    2: "#42c6ff",
    3: "#ffd166",
    4: "#ff8c42",
    5: "#ff416c",
}

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

WHITE = "#f8fafc"
INK = "#061019"
BODY = "#081722"
BODY_TOP = "#102a3a"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/DejaVuSans-Bold.ttf"),
    ):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _box(values: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return tuple(round(value * SCALE) for value in values)  # type: ignore[return-value]


def _points(values: list[tuple[float, float]]) -> list[tuple[int, int]]:
    return [(round(x * SCALE), round(y * SCALE)) for x, y in values]


def _line(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    fill: str,
    width: float = 1.0,
    under: str = INK,
    under_width: float | None = None,
) -> None:
    scaled = _points(points)
    if under_width is None:
        under_width = width + 1.0
    if under_width > width:
        draw.line(scaled, fill=under, width=max(1, round(under_width * SCALE)), joint="curve")
    draw.line(scaled, fill=fill, width=max(1, round(width * SCALE)), joint="curve")


SUBJECT_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("child", re.compile(r"child|boy|girl|baby|infant|teenager|youth|pupil|easter bunny", re.I)),
    ("hospital", re.compile(r"hospital|care home|nursing home|medical centre|gp surgery", re.I)),
    ("school", re.compile(r"school|university|college|nursery", re.I)),
    ("prison", re.compile(r"prison|custody|cell block", re.I)),
    ("hotel", re.compile(r"hotel|hostel", re.I)),
    ("retail", re.compile(r"shopping centre|\b(?:supermarket|shop|market|store|bakery|restaurant|pub|nightclub)\b", re.I)),
    ("industrial", re.compile(r"factory|warehouse|industrial|manufacturing|machine|workshop|power station|substation|plant|silo|building site|dryer|appliance", re.I)),
    ("public_building", re.compile(r"museum|town hall|heritage building|office building|company premises|control tower|fire station", re.I)),
    ("alarm", re.compile(r"alarm activation|smoke alarm|panic button|premise alarm", re.I)),
    ("infrastructure", re.compile(r"phonebox|postbox|manhole|hydrant|electrical cable|powerline|pipeline|pipe burst|installation|gutter", re.I)),
    ("container", re.compile(r"container|cylinder|battery", re.I)),
    ("food", re.compile(r"grease|kitchen|barbecue|bbq|food|cake|chocolate|pumpkin soup|picnic|candle light dinner|bouquet", re.I)),
    ("sports", re.compile(r"sports hall|athlete|gymnast|goal|corner flag|pitch|spectator stand", re.I)),
    ("camp", re.compile(r"camp|tent", re.I)),
    ("home", re.compile(r"house|home|flat|room|garage|shed|cottage|basement|chimney|roof|balcony|residential", re.I)),
    ("hgv", re.compile(r"\b(?:hgv|truck|lorry|tanker|tractor|trailer|harvester)\b", re.I)),
    ("bus", re.compile(r"\b(?:bus|buses|coach|coaches)\b", re.I)),
    ("motorbike", re.compile(r"\b(?:motorbike|motorcycle|e-scooter|scooter)\b", re.I)),
    ("cyclist", re.compile(r"\b(?:cyclist|bicycle|bike rider)\b", re.I)),
    ("vehicle", re.compile(r"\b(?:car|vehicle|van|caravan|camper)\b", re.I)),
    ("rail", re.compile(r"\b(?:train|tram|locomotive)\b|\brail(?:way)?\b", re.I)),
    ("aircraft", re.compile(r"\b(?:aircraft|aeroplane|airplane|plane|helicopter|airfield|airport|runway)\b", re.I)),
    ("vessel", re.compile(r"boat|ship|vessel|yacht|canoe|kayak|lifeboat|jet ski|ferry", re.I)),
    ("water", re.compile(r"\b(?:water|sea|beach|river|harbour|offshore)\b|coast(?:line)?|drown|swim|flood", re.I)),
    ("animal", re.compile(r"\b(?:animal|dog|cat|horse|swan|bird|livestock|deer|rabbit|cow|sheep|goat|snake|reindeer|stable|stables)\b", re.I)),
    ("forest", re.compile(r"\b(?:forest|woodland|heathland|moorland|terrain|tree|hedge|grass|field|farmland|leaves|straw|hay)\b", re.I)),
    ("waste", re.compile(r"\b(?:bin|rubbish|waste|landfill|recycling|manure|tyres)\b", re.I)),
    ("height", re.compile(r"height|cliff|crane|mast|scaffold|ravine|cave|mineshaft|mountain|roof", re.I)),
    ("crowd", re.compile(r"crowd|demonstration|protest|party|rave|event|match|game|stadium|festival|parade|fan|pitch invader|stands", re.I)),
    ("person", re.compile(r"\b(?:person|adult|patient|driver|employee|worker|guest|resident|official|suspect)\b", re.I)),
]

MEDICAL_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("heart", re.compile(r"cardiac|heart|chest pain|chest tight|palpitation", re.I)),
    ("lungs", re.compile(r"breath|asthma|respiratory|choking|copd|smoke inhal", re.I)),
    ("brain", re.compile(r"seizure|stroke|ischemic|dementia|unconscious|head injur|confusion|altered consciousness|facial droop|vertigo|one sided weakness|slurred speech|delirium", re.I)),
    ("blood", re.compile(r"bleed|haemorrhage|hemorrhage|nosebleed|hypovolemic|vomiting blood", re.I)),
    ("bone", re.compile(r"fracture|broken|sprain|spinal|back pain|limb|amputation|dislocation|penetrating trauma|wound|injury", re.I)),
    ("maternity", re.compile(r"labour|birth|pregnan|maternity|waters broken", re.I)),
    ("allergy", re.compile(r"allerg|anaphyla", re.I)),
    ("poison", re.compile(r"intoxic|overdose|poison|alcohol|drug|ate too much", re.I)),
    ("burn", re.compile(r"burn|scald|heatstroke|sunstroke|electrocution", re.I)),
    ("fall", re.compile(r"fall|fallen|slip|trip", re.I)),
    ("infection", re.compile(r"fever|infection|sepsis|\buti\b|sore throat", re.I)),
    ("digestive", re.compile(r"stomach|abdominal|vomit|cramp|butterflies", re.I)),
    ("diabetes", re.compile(r"diabet", re.I)),
    ("bite", re.compile(r"bite|sting|wasp|bee|insect", re.I)),
    ("eye", re.compile(r"blurred vision|eye injur", re.I)),
]


def _subject_for(name: str) -> str:
    for subject, pattern in SUBJECT_RULES:
        if pattern.search(name):
            return subject
    return "response"


def _modifier_for(name: str, family: str) -> str:
    if family in {"medical", "cardiac"}:
        for modifier, pattern in MEDICAL_RULES:
            if pattern.search(name):
                return modifier
        return "medical"
    if re.search(r"persons? reported|people reported", name, re.I):
        return "persons_reported"
    if re.search(r"trapped|entrapment|stuck|stranded|collapse", name, re.I):
        return "trapped"
    if re.search(r"missing|search for|concern for welfare|lost child", name, re.I):
        return "search"
    if re.search(r"explosion|exploded|flashover", name, re.I):
        return "explosion"
    if re.search(r"spill|leak|gas alarm|chemical|chlorine|ammonia|fuel", name, re.I):
        return "chemical"
    if re.search(r"flood|water rescue|drown|swimmer", name, re.I):
        return "water"
    if re.search(r"weapon|knife|firearm|gun|shoot|armed", name, re.I):
        return "weapon"
    if re.search(r"theft|stolen|robbery|burglary|shoplifting|heist|pickpocket|fraud|forgery", name, re.I):
        return "theft"
    if re.search(r"fight|brawl|riot|violence|assault|aggressive|disorder", name, re.I):
        return "violence"
    if re.search(r"derail|collid|collision|accident|crash|hit and run|hit by|struck|rollover|overturn", name, re.I):
        return "collision"
    if re.search(r"fire|burning|blaze|smoke|ignited|bonfire", name, re.I):
        return "fire"
    if re.search(r"wind|storm|snow|ice|lightning|weather", name, re.I):
        return "weather"
    if re.search(r"fall|fallen|height|cliff|crane|mast|scaffold|roof", name, re.I):
        return "height"
    if re.search(r"animal|dog|cat|horse|swan|bird|livestock|deer|rabbit|cow", name, re.I):
        return "animal"
    if re.search(r"protest|demonstration|crowd|party|rave|event|match|game|parade|fan|pitch invader|stands", name, re.I):
        return "crowd"
    if re.search(r"traffic stop|speed enforcement|speed detection|live lane|fail to stop|anpr", name, re.I):
        return "traffic"
    if re.search(r"alarm|panic button", name, re.I):
        return "alarm"
    return family if family != "response" else "response"


def signature_for(name: str, family: str) -> dict[str, str]:
    """Return semantic layers used to compose a stable mission signature."""
    modifier = _modifier_for(name, family)
    subject = _subject_for(name)
    return {
        "modifier": modifier,
        "subject": subject,
        "signature": f"{family}:{modifier}:{subject}",
    }


def _ordered_services(primary: str, services: list[str]) -> list[str]:
    values = [service for service in services if service in SERVICE_COLOURS and service != "mixed"]
    result: list[str] = []
    if primary in SERVICE_COLOURS and primary != "mixed":
        result.append(primary)
    for service in values:
        if service not in result:
            result.append(service)
    return (result or ["mixed"])[:3]


def _state_glyph(draw: ImageDraw.ImageDraw, state: str) -> None:
    colour = STATES[state]
    if state == "yellow":
        diamond = _points([(5.8, 2.0), (9.5, 5.7), (5.8, 9.4), (2.1, 5.7)])
        draw.polygon(diamond, fill=colour)
        _line(draw, [(4.4, 4.2), (6.0, 5.7), (4.4, 7.2)], INK, 0.75, colour, 0.75)
        _line(draw, [(6.0, 4.2), (7.7, 5.7), (6.0, 7.2)], INK, 0.75, colour, 0.75)
        return
    draw.ellipse(_box((2.0, 2.0, 9.5, 9.5)), fill=colour, outline=WHITE, width=round(0.65 * SCALE))
    if state == "red":
        draw.rounded_rectangle(_box((5.25, 3.3, 6.25, 6.8)), radius=round(0.4 * SCALE), fill="#ffffff")
        draw.ellipse(_box((5.2, 7.2, 6.3, 8.3)), fill="#ffffff")
    else:
        _line(draw, [(3.8, 5.8), (5.3, 7.25), (8.0, 4.2)], "#ffffff", 0.9, "#ffffff", 0.9)


def _level_badge(draw: ImageDraw.ImageDraw, level: int) -> None:
    colour = LEVEL_COLOURS[level]
    shield = _points([(21.5, 1.2), (30.7, 1.2), (30.7, 7.7), (26.1, 12.0), (21.5, 7.7)])
    draw.polygon(shield, fill=INK)
    draw.line(shield + [shield[0]], fill=colour, width=round(1.25 * SCALE), joint="curve")
    fnt = _font(8 * SCALE)
    value = str(level)
    box = draw.textbbox((0, 0), value, font=fnt)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text((26.1 * SCALE - tw / 2, 5.4 * SCALE - th / 2 - box[1]), value, font=fnt, fill="#ffffff")


def _service_rail(draw: ImageDraw.ImageDraw, services: list[str]) -> None:
    top, bottom, gap = 11.0, 28.9, 0.7
    height = (bottom - top - gap * (len(services) - 1)) / len(services)
    for index, service in enumerate(services):
        y1 = top + index * (height + gap)
        y2 = y1 + height
        draw.rounded_rectangle(_box((2.1, y1, 4.7, y2)), radius=round(0.9 * SCALE), fill=SERVICE_COLOURS[service])


def _base_pictogram(draw: ImageDraw.ImageDraw, family: str, accent: str) -> None:
    if family == "fire":
        draw.polygon(_points([(14, 28), (9, 24), (10, 18), (15, 11), (15, 18), (20, 14), (21, 22), (18, 28)]), fill=accent)
        draw.polygon(_points([(15, 26), (12, 23), (15, 18), (18, 23)]), fill=WHITE)
    elif family in {"police", "crime"}:
        draw.rounded_rectangle(_box((9, 12, 21, 27)), radius=3 * SCALE, outline=accent, width=2 * SCALE)
        draw.polygon(_points([(15, 15), (17, 20), (21, 20), (18, 22), (19, 26), (15, 24), (11, 26), (12, 22), (9, 20), (13, 20)]), fill=WHITE)
    elif family in {"medical", "cardiac"}:
        _medical_pictogram(draw, "heart" if family == "cardiac" else "medical", accent)
    elif family == "collision":
        draw.rounded_rectangle(_box((7.5, 18, 14.5, 24)), radius=SCALE, outline=WHITE, width=round(1.5 * SCALE))
        draw.rounded_rectangle(_box((17.5, 16, 24, 23)), radius=SCALE, outline=accent, width=round(1.5 * SCALE))
        _line(draw, [(14, 17), (16, 19), (18, 16)], "#ffd166", 1.0)
        draw.ellipse(_box((8.5, 23, 11.5, 26)), fill=WHITE)
        draw.ellipse(_box((20, 22, 23, 25)), fill=accent)
    elif family == "aircraft":
        draw.polygon(_points([(15, 10), (18, 19), (24, 22), (24, 24), (17, 23), (17, 28), (20, 30), (20, 31), (15, 30), (10, 31), (10, 30), (13, 28), (13, 23), (7, 24), (7, 22), (13, 19)]), fill=accent)
    elif family == "rail":
        draw.rounded_rectangle(_box((9, 11, 21, 26)), radius=2 * SCALE, outline=accent, width=2 * SCALE)
        draw.rectangle(_box((11, 14, 19, 18)), fill=WHITE)
        draw.ellipse(_box((11, 22, 14, 25)), fill=WHITE)
        draw.ellipse(_box((17, 22, 20, 25)), fill=WHITE)
        _line(draw, [(11, 28), (14, 25), (17, 25), (20, 28)], WHITE, 1.0)
    elif family == "marine":
        draw.polygon(_points([(8, 21), (23, 21), (20, 26), (11, 26)]), fill=accent)
        draw.rectangle(_box((14, 15, 18, 21)), fill=WHITE)
        draw.polygon(_points([(18, 15), (22, 19), (18, 19)]), fill=WHITE)
        _line(draw, [(7, 28), (11, 27), (15, 28), (19, 27), (23, 28)], WHITE, 1.0)
    elif family == "mountain":
        draw.polygon(_points([(7, 27), (14, 12), (19, 21), (22, 16), (25, 27)]), fill=accent)
        draw.polygon(_points([(12, 17), (14, 12), (17, 18), (15, 17), (14, 20)]), fill=WHITE)
    elif family == "hazmat":
        draw.ellipse(_box((9, 13, 21, 25)), outline=accent, width=2 * SCALE)
        for angle in (0, 120, 240):
            radians = math.radians(angle)
            x = 15 + math.cos(radians) * 5
            y = 19 + math.sin(radians) * 5
            draw.ellipse(_box((x - 2, y - 2, x + 2, y + 2)), fill=WHITE)
        draw.ellipse(_box((13, 17, 17, 21)), fill=accent)
    elif family == "eod":
        draw.ellipse(_box((10, 15, 21, 27)), fill=accent)
        _line(draw, [(15, 15), (18, 11), (21, 12)], WHITE, 1.0)
        draw.ellipse(_box((20, 10, 23, 13)), fill="#ffd166")
    elif family == "collapse":
        draw.polygon(_points([(8, 15), (14, 11), (14, 27), (8, 27)]), fill=accent)
        draw.polygon(_points([(16, 12), (23, 15), (23, 27), (17, 27)]), fill=WHITE)
        _line(draw, [(15, 13), (17, 17), (14, 20), (17, 24), (15, 28)], "#ff8c42", 1.0)
    elif family == "weather":
        draw.ellipse(_box((8, 17, 18, 25)), fill=WHITE)
        draw.ellipse(_box((14, 14, 24, 25)), fill=accent)
        draw.rectangle(_box((9, 20, 23, 25)), fill=accent)
        _line(draw, [(11, 28), (10, 31)], "#42c6ff", 1.0)
        _line(draw, [(17, 28), (16, 31)], "#42c6ff", 1.0)
        _line(draw, [(22, 28), (21, 31)], "#42c6ff", 1.0)
    elif family == "animal":
        draw.ellipse(_box((10, 18, 21, 28)), fill=accent)
        for x, y in ((10, 15), (15, 13), (20, 15), (23, 19)):
            draw.ellipse(_box((x - 2, y - 2, x + 2, y + 2)), fill=WHITE)
    elif family == "crowd":
        for x, y, colour in ((10, 17, WHITE), (16, 14, accent), (22, 17, WHITE)):
            draw.ellipse(_box((x - 2, y - 2, x + 2, y + 2)), fill=colour)
            draw.rounded_rectangle(_box((x - 3, y + 2, x + 3, y + 10)), radius=2 * SCALE, fill=colour)
    elif family == "utilities":
        draw.polygon(_points([(17, 10), (10, 22), (15, 22), (12, 31), (22, 18), (17, 18)]), fill="#ffd166")
    elif family == "rescue":
        draw.ellipse(_box((13, 11, 18, 16)), fill=WHITE)
        _line(draw, [(15, 16), (15, 24), (10, 28)], WHITE, 1.7)
        _line(draw, [(15, 20), (21, 17)], accent, 1.7)
        _line(draw, [(15, 24), (21, 29)], accent, 1.7)
        draw.ellipse(_box((8, 26, 12, 30)), outline=accent, width=SCALE)
    else:
        draw.rounded_rectangle(_box((9, 13, 21, 27)), radius=4 * SCALE, outline=accent, width=2 * SCALE)
        draw.rectangle(_box((13, 16, 17, 24)), fill=WHITE)
        draw.rectangle(_box((11, 18, 19, 22)), fill=WHITE)


def _medical_pictogram(draw: ImageDraw.ImageDraw, modifier: str, accent: str) -> None:
    if modifier == "heart":
        draw.polygon(_points([(15.5, 27.1), (8.4, 20.3), (9.2, 14.8), (13.5, 13.2), (15.6, 16.0), (18.0, 13.2), (22.3, 14.8), (22.8, 20.0)]), fill=accent)
        _line(draw, [(8.6, 21.2), (12.0, 21.2), (13.4, 18.0), (15.2, 24.4), (17.2, 19.8), (19.0, 21.2), (23.2, 21.2)], WHITE, 1.0)
    elif modifier == "lungs":
        _line(draw, [(15.5, 12), (15.5, 19)], WHITE, 1.2)
        draw.ellipse(_box((8.5, 16, 15.0, 27)), fill=accent)
        draw.ellipse(_box((16.0, 16, 22.5, 27)), fill=accent)
        _line(draw, [(15.5, 18), (12.7, 21.0)], WHITE, 0.8)
        _line(draw, [(15.5, 18), (18.5, 21.0)], WHITE, 0.8)
    elif modifier == "brain":
        draw.ellipse(_box((8.5, 13, 22.5, 27)), fill=accent, outline=WHITE, width=round(1.0 * SCALE))
        _line(draw, [(15.5, 14), (15.5, 26)], INK, 0.8, accent, 0.8)
        _line(draw, [(10.5, 18), (13.5, 17), (12.0, 21), (14.5, 23)], WHITE, 0.7, accent, 0.7)
        _line(draw, [(20.5, 18), (17.5, 17), (19.0, 21), (16.5, 23)], WHITE, 0.7, accent, 0.7)
    elif modifier == "blood":
        draw.polygon(_points([(15.5, 11), (9.0, 21), (10.5, 26), (15.5, 29), (20.5, 26), (22.0, 21)]), fill=accent)
        draw.ellipse(_box((13, 20, 16, 23)), fill=WHITE)
    elif modifier == "bone":
        _line(draw, [(11, 25), (20, 15)], WHITE, 2.0)
        for x, y in ((10, 26), (12, 27), (19, 14), (21, 15)):
            draw.ellipse(_box((x - 1.7, y - 1.7, x + 1.7, y + 1.7)), fill=accent)
    elif modifier == "maternity":
        draw.ellipse(_box((11.0, 11.5, 16.0, 16.5)), fill=WHITE)
        draw.ellipse(_box((10.0, 16.0, 21.5, 28.0)), fill=accent)
        draw.ellipse(_box((14.5, 18.5, 19.5, 23.5)), fill=BODY)
        draw.ellipse(_box((16.0, 19.5, 18.0, 21.5)), fill=WHITE)
    elif modifier == "allergy":
        draw.polygon(_points([(15.5, 10.5), (24.0, 27.5), (7.0, 27.5)]), fill=accent)
        draw.rounded_rectangle(_box((14.6, 15.0, 16.4, 22.0)), radius=round(0.6 * SCALE), fill=INK)
        draw.ellipse(_box((14.5, 23.4, 16.5, 25.4)), fill=INK)
    elif modifier == "poison":
        draw.ellipse(_box((10.0, 12.0, 21.0, 23.0)), fill=WHITE)
        draw.ellipse(_box((12.2, 15.0, 14.5, 17.3)), fill=INK)
        draw.ellipse(_box((17.0, 15.0, 19.3, 17.3)), fill=INK)
        _line(draw, [(13.0, 20.0), (18.5, 20.0)], INK, 0.8, WHITE, 0.8)
        _line(draw, [(10.5, 25.5), (20.5, 29.0)], accent, 1.3)
        _line(draw, [(20.5, 25.5), (10.5, 29.0)], accent, 1.3)
    elif modifier == "burn":
        draw.polygon(_points([(15.5, 29), (9.5, 24), (10.5, 18), (15.5, 11), (15.5, 18), (20.5, 14), (21.5, 23)]), fill=accent)
        draw.polygon(_points([(15.5, 27), (12.5, 23), (15.5, 18), (18.5, 23)]), fill=WHITE)
    elif modifier == "fall":
        draw.ellipse(_box((12.8, 11, 17.5, 15.7)), fill=WHITE)
        _line(draw, [(15, 16), (17, 22), (22, 24)], accent, 1.5)
        _line(draw, [(17, 20), (11, 22)], WHITE, 1.3)
        _line(draw, [(17, 22), (13, 28)], WHITE, 1.3)
        _line(draw, [(17, 22), (22, 28)], accent, 1.3)
    elif modifier == "infection":
        draw.ellipse(_box((10, 14, 21, 25)), fill=accent)
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            x1, y1 = 15.5 + math.cos(radians) * 5, 19.5 + math.sin(radians) * 5
            x2, y2 = 15.5 + math.cos(radians) * 8, 19.5 + math.sin(radians) * 8
            _line(draw, [(x1, y1), (x2, y2)], WHITE, 0.7, accent, 0.7)
        draw.ellipse(_box((13.5, 17.5, 15.5, 19.5)), fill=WHITE)
        draw.ellipse(_box((17.0, 20.0, 19.0, 22.0)), fill=WHITE)
    elif modifier == "digestive":
        _line(draw, [(13.0, 12.0), (13.0, 17.0), (16.5, 19.0), (19.5, 17.0), (21.0, 20.0), (19.0, 27.0), (12.0, 27.0), (10.0, 23.0), (12.5, 20.0)], accent, 1.8)
        draw.ellipse(_box((14.0, 21.0, 17.0, 24.0)), fill=WHITE)
    elif modifier == "diabetes":
        draw.polygon(_points([(15.5, 10.8), (9.5, 21.0), (11.0, 26.5), (15.5, 29.0), (20.0, 26.5), (21.5, 21.0)]), fill=accent)
        draw.rectangle(_box((14.4, 16.3, 16.6, 24.0)), fill=WHITE)
        draw.rectangle(_box((11.8, 19.0, 19.2, 21.2)), fill=WHITE)
    elif modifier == "bite":
        draw.ellipse(_box((9.5, 13.5, 21.5, 27.0)), outline=accent, width=round(1.6 * SCALE))
        for x, y in ((11.0, 16.5), (14.0, 14.5), (18.0, 15.0), (20.3, 18.0), (11.0, 23.0), (14.0, 26.0), (18.0, 25.5), (20.3, 22.5)):
            draw.ellipse(_box((x - 0.8, y - 0.8, x + 0.8, y + 0.8)), fill=WHITE)
    elif modifier == "eye":
        draw.polygon(_points([(7.5, 20.5), (11.5, 16.5), (15.5, 15.0), (19.5, 16.5), (23.5, 20.5), (19.5, 24.5), (15.5, 26.0), (11.5, 24.5)]), fill=WHITE)
        draw.ellipse(_box((12.3, 17.3, 18.7, 23.7)), fill=accent)
        draw.ellipse(_box((14.3, 19.3, 16.7, 21.7)), fill=INK)
    else:
        draw.rounded_rectangle(_box((9, 13, 21, 27)), radius=3 * SCALE, outline=accent, width=2 * SCALE)
        draw.rectangle(_box((13, 16, 17, 24)), fill=WHITE)
        draw.rectangle(_box((11, 18, 19, 22)), fill=WHITE)


def _child_search(draw: ImageDraw.ImageDraw, accent: str) -> None:
    draw.ellipse(_box((10.3, 11.0, 18.9, 19.6)), outline=accent, width=round(1.7 * SCALE))
    _line(draw, [(17.4, 18.2), (21.6, 22.6)], accent, 1.8)
    draw.ellipse(_box((13.1, 12.5, 16.2, 15.6)), fill=WHITE)
    draw.rounded_rectangle(_box((12.6, 15.8, 16.7, 21.4)), radius=round(1.1 * SCALE), fill=WHITE)
    _line(draw, [(13.4, 20.6), (11.8, 24.0)], WHITE, 1.0)
    _line(draw, [(15.9, 20.6), (17.8, 24.0)], WHITE, 1.0)
    _line(draw, [(11.7, 26.3), (14.2, 25.4), (16.7, 26.3), (19.2, 25.4), (21.7, 26.3)], accent, 1.1)


def _fire_person(draw: ImageDraw.ImageDraw, accent: str) -> None:
    draw.polygon(_points([(12.5, 27.0), (8.0, 23.0), (9.3, 17.0), (14.2, 10.7), (14.4, 17.3), (18.4, 14.0), (20.0, 21.8), (17.2, 27.0)]), fill=accent)
    draw.polygon(_points([(13.7, 25.8), (11.5, 22.5), (14.5, 17.9), (17.2, 22.6)]), fill="#fff2df")
    draw.ellipse(_box((19.4, 17.1, 22.2, 19.9)), fill="#ffffff")
    _line(draw, [(20.8, 19.6), (20.8, 25.2)], "#ffffff", 1.0)
    draw.polygon(_points([(23.2, 14.0), (25.2, 17.5), (21.2, 17.5)]), fill="#ffd166")


def _rtc_entrapment(draw: ImageDraw.ImageDraw, accent: str) -> None:
    draw.rounded_rectangle(_box((7.0, 17.2, 14.7, 23.6)), radius=round(1.1 * SCALE), outline=WHITE, width=round(1.5 * SCALE))
    draw.rounded_rectangle(_box((17.3, 15.4, 24.3, 22.2)), radius=round(1.1 * SCALE), outline=accent, width=round(1.5 * SCALE))
    draw.ellipse(_box((8.2, 22.4, 11.0, 25.2)), fill=WHITE)
    draw.ellipse(_box((20.2, 21.2, 23.0, 24.0)), fill=accent)
    draw.polygon(_points([(14.2, 14.7), (16.0, 17.7), (17.8, 14.7), (17.1, 19.0), (20.0, 18.5), (16.5, 21.1), (13.5, 18.5), (15.1, 18.9)]), fill="#ffd166")
    _line(draw, [(10.0, 28.0), (15.8, 24.2), (21.4, 28.0)], "#b88cff", 1.0)


def _modifier_badge(draw: ImageDraw.ImageDraw, modifier: str, subject: str, accent: str) -> None:
    # A secondary semantic token occupies a protected lower-right capsule.
    token = subject if subject != "response" else modifier
    if token in {"response", "medical", "fire", "collision"}:
        return
    draw.ellipse(_box((20.1, 22.0, 28.2, 30.1)), fill=INK, outline=accent, width=round(0.8 * SCALE))
    if token in {"person", "child"}:
        head = (22.7, 23.2, 25.4, 25.9) if token == "person" else (22.9, 23.5, 25.2, 25.8)
        draw.ellipse(_box(head), fill=WHITE)
        _line(draw, [(24.05, 26.0), (24.05, 28.5)], WHITE, 0.8, WHITE, 0.8)
    elif token in {"home", "hotel", "retail", "school", "hospital", "industrial", "prison", "public_building"}:
        draw.polygon(_points([(21.4, 25.2), (24.2, 22.9), (27.0, 25.2)]), fill=accent)
        draw.rectangle(_box((22.1, 25.0, 26.3, 28.6)), fill=WHITE)
        if token == "hospital":
            draw.rectangle(_box((23.7, 25.3, 24.7, 28.2)), fill=accent)
            draw.rectangle(_box((22.8, 26.2, 25.6, 27.2)), fill=accent)
        elif token == "prison":
            for x in (23.0, 24.2, 25.4):
                _line(draw, [(x, 25.2), (x, 28.5)], INK, 0.45, INK, 0.45)
    elif token in {"vehicle", "hgv", "bus", "motorbike", "cyclist"}:
        if token in {"motorbike", "cyclist"}:
            draw.ellipse(_box((21.4, 26.3, 23.7, 28.6)), outline=WHITE, width=round(0.55 * SCALE))
            draw.ellipse(_box((25.1, 26.3, 27.4, 28.6)), outline=WHITE, width=round(0.55 * SCALE))
            _line(draw, [(22.5, 27.3), (24.2, 24.8), (26.2, 27.3), (23.4, 27.3)], accent, 0.55, accent, 0.55)
        else:
            draw.rounded_rectangle(_box((21.2, 24.5, 27.2, 28.0)), radius=round(0.7 * SCALE), fill=accent)
            draw.ellipse(_box((22.0, 27.3, 23.5, 28.8)), fill=WHITE)
            draw.ellipse(_box((25.0, 27.3, 26.5, 28.8)), fill=WHITE)
    elif token in {"water", "vessel"}:
        if token == "vessel":
            draw.polygon(_points([(21.5, 25.5), (27.0, 25.5), (26.0, 27.5), (22.5, 27.5)]), fill=accent)
        _line(draw, [(21.4, 28.4), (23.0, 27.8), (24.5, 28.4), (26.0, 27.8), (27.5, 28.4)], WHITE, 0.6, WHITE, 0.6)
    elif token in {"rail", "aircraft"}:
        if token == "aircraft":
            draw.polygon(_points([(24.1, 22.8), (25.0, 25.7), (27.2, 26.8), (25.0, 26.6), (24.5, 29.0), (23.7, 26.6), (21.5, 26.8), (23.6, 25.7)]), fill=WHITE)
        else:
            draw.rounded_rectangle(_box((22.1, 23.2, 26.4, 27.8)), radius=round(0.7 * SCALE), outline=WHITE, width=round(0.6 * SCALE))
            _line(draw, [(22.0, 29.0), (23.5, 27.5), (25.0, 27.5), (26.6, 29.0)], accent, 0.5, accent, 0.5)
    elif token in {"animal", "forest", "waste"}:
        if token == "animal":
            draw.ellipse(_box((22.6, 25.4, 25.7, 28.4)), fill=accent)
            for x, y in ((22.0, 24.5), (23.5, 23.8), (25.0, 24.0), (26.2, 24.9)):
                draw.ellipse(_box((x - 0.7, y - 0.7, x + 0.7, y + 0.7)), fill=WHITE)
        elif token == "forest":
            draw.polygon(_points([(24.1, 22.8), (21.2, 27.4), (27.0, 27.4)]), fill=accent)
            draw.rectangle(_box((23.6, 27.0, 24.6, 29.0)), fill=WHITE)
        else:
            draw.rectangle(_box((22.0, 24.5, 26.5, 28.5)), fill=accent)
            _line(draw, [(21.5, 24.2), (27.0, 24.2)], WHITE, 0.6, WHITE, 0.6)
    elif token in {"height", "trapped"}:
        if token == "trapped":
            for x in (22.0, 24.0, 26.0):
                _line(draw, [(x, 23.3), (x, 28.8)], WHITE, 0.55, WHITE, 0.55)
        else:
            draw.polygon(_points([(24.1, 22.9), (27.2, 28.4), (21.0, 28.4)]), fill=accent)
            _line(draw, [(24.1, 27.4), (24.1, 24.4)], WHITE, 0.6, WHITE, 0.6)
    elif token in {"crowd", "violence"}:
        for x, y in ((22.0, 25.0), (24.2, 23.7), (26.4, 25.0)):
            draw.ellipse(_box((x - 0.8, y - 0.8, x + 0.8, y + 0.8)), fill=WHITE)
        if token == "violence":
            draw.polygon(_points([(24.2, 26.0), (25.0, 27.4), (26.6, 27.0), (25.3, 28.7), (23.2, 28.2)]), fill=accent)
    elif token in {"weapon", "theft"}:
        if token == "weapon":
            _line(draw, [(21.8, 28.4), (26.7, 23.4)], WHITE, 1.0)
            draw.polygon(_points([(26.0, 22.8), (27.5, 22.8), (27.1, 24.3)]), fill=accent)
        else:
            draw.rounded_rectangle(_box((21.8, 24.6, 26.8, 28.8)), radius=round(0.7 * SCALE), fill=accent)
            _line(draw, [(23.0, 24.8), (24.3, 22.9), (25.6, 24.8)], WHITE, 0.6, WHITE, 0.6)
    elif token in {"chemical", "fuel"}:
        draw.polygon(_points([(24.2, 22.7), (21.8, 26.3), (22.4, 28.4), (24.2, 29.2), (26.0, 28.4), (26.6, 26.3)]), fill=accent)
    elif token in {"weather", "explosion"}:
        if token == "explosion":
            draw.polygon(_points([(24.1, 22.7), (24.8, 24.5), (27.1, 23.8), (26.1, 26.0), (27.5, 27.6), (25.0, 27.2), (24.2, 29.2), (23.4, 27.2), (21.0, 27.8), (22.3, 25.9), (21.3, 24.0), (23.5, 24.6)]), fill="#ffd166")
        else:
            draw.ellipse(_box((21.7, 24.1, 25.0, 27.3)), fill=WHITE)
            draw.ellipse(_box((23.5, 23.1, 27.2, 27.3)), fill=accent)
            _line(draw, [(23.0, 28.5), (22.5, 29.4)], "#42c6ff", 0.5, "#42c6ff", 0.5)
    elif token == "infrastructure":
        draw.polygon(_points([(25.0, 22.6), (21.5, 26.7), (24.0, 26.7), (22.8, 29.5), (27.0, 25.2), (24.8, 25.2)]), fill="#ffd166")
    elif token == "container":
        draw.rectangle(_box((21.7, 23.8, 26.8, 28.7)), fill=accent, outline=WHITE, width=round(0.55 * SCALE))
        _line(draw, [(24.25, 24.0), (24.25, 28.5)], WHITE, 0.45, WHITE, 0.45)
    elif token == "food":
        draw.arc(_box((21.0, 23.0, 27.2, 28.8)), start=0, end=180, fill=accent, width=round(0.8 * SCALE))
        _line(draw, [(21.6, 26.1), (26.6, 26.1)], WHITE, 0.55, WHITE, 0.55)
        _line(draw, [(24.0, 22.8), (25.0, 24.8)], accent, 0.55, accent, 0.55)
    elif token == "sports":
        draw.ellipse(_box((21.4, 23.2, 27.0, 28.8)), fill=WHITE, outline=accent, width=round(0.55 * SCALE))
        draw.polygon(_points([(24.2, 24.7), (25.2, 25.4), (24.8, 26.6), (23.6, 26.6), (23.2, 25.4)]), fill=accent)
    elif token == "camp":
        draw.polygon(_points([(24.1, 22.8), (27.2, 28.6), (21.0, 28.6)]), fill=accent)
        draw.polygon(_points([(24.1, 24.7), (25.3, 28.4), (23.0, 28.4)]), fill=INK)
    elif token == "alarm":
        draw.polygon(_points([(24.2, 22.9), (27.0, 28.4), (21.4, 28.4)]), fill=accent)
        draw.rounded_rectangle(_box((23.7, 24.5, 24.7, 26.8)), radius=round(0.3 * SCALE), fill=INK)
        draw.ellipse(_box((23.6, 27.3, 24.8, 28.5)), fill=INK)
    elif token == "traffic":
        _line(draw, [(21.4, 28.6), (24.2, 23.0), (27.0, 28.6)], WHITE, 0.7, WHITE, 0.7)
        _line(draw, [(24.2, 24.1), (24.2, 25.2)], accent, 0.55, accent, 0.55)
        _line(draw, [(24.2, 26.4), (24.2, 27.5)], accent, 0.55, accent, 0.55)


def render_icon(
    state: str,
    level: int,
    primary_service: str,
    services: list[str],
    family: str,
    modifier: str,
    subject: str,
) -> Image.Image:
    """Render one 32x37 status marker using the V2 operational grammar."""
    image = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    state_colour = STATES[state]
    ordered_services = _ordered_services(primary_service, services)
    accent = SERVICE_COLOURS[ordered_services[0]]

    # High-contrast pin silhouette, light keyline, state halo and pointed state tail.
    draw.polygon(_points([(12.3, 31.0), (19.7, 31.0), (16.0, 36.3)]), fill=WHITE)
    draw.polygon(_points([(13.0, 31.0), (19.0, 31.0), (16.0, 35.4)]), fill=state_colour)
    draw.rounded_rectangle(_box((0.7, 0.7, 31.3, 33.2)), radius=round(5.5 * SCALE), fill=WHITE)
    draw.rounded_rectangle(_box((1.35, 1.35, 30.65, 32.55)), radius=round(4.9 * SCALE), fill=state_colour)
    draw.rounded_rectangle(_box((2.7, 2.7, 29.3, 31.2)), radius=round(3.8 * SCALE), fill=BODY)
    draw.rounded_rectangle(_box((3.4, 3.4, 28.6, 14.0)), radius=round(3.0 * SCALE), fill=BODY_TOP)
    draw.rectangle(_box((3.4, 11.2, 28.6, 14.1)), fill="#0d2230")

    _state_glyph(draw, state)
    _level_badge(draw, level)
    _service_rail(draw, ordered_services)

    if family == "marine" and modifier == "search" and subject in {"child", "person", "water"}:
        _child_search(draw, accent)
    elif family == "fire" and modifier == "persons_reported":
        _fire_person(draw, accent)
    elif family == "collision" and modifier == "trapped":
        _rtc_entrapment(draw, accent)
    elif family in {"medical", "cardiac"}:
        _medical_pictogram(draw, modifier, accent)
    else:
        _base_pictogram(draw, family, accent)
        _modifier_badge(draw, modifier, subject, accent)

    # Familiar lower state band remains the fastest colour-state cue.
    draw.rounded_rectangle(_box((6.0, 29.1, 26.7, 31.4)), radius=round(1.0 * SCALE), fill=state_colour)
    rendered = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    # Keep the bounding-box corners truly transparent after antialiasing.
    for coordinate in ((0, 0), (WIDTH - 1, 0)):
        rendered.putpixel(coordinate, (0, 0, 0, 0))
    return rendered
