#!/usr/bin/env python3
"""Operational V4 premium illustrated-scene renderer.

V4 replaces the rejected V3 centre pictograms with curated high-detail scene
masters.  Status, response level, service mix and native-row identity remain
deterministic so the complete pack can be rebuilt and audited offline.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from icon_style_v2 import LEVEL_COLOURS, signature_for


WIDTH = 64
HEIGHT = 83
MASTER_WIDTH = 96
MASTER_HEIGHT = 124
STYLE_VERSION = "4.0"
STYLE_FEATURES = [
    "premium_illustrated_scene_masters",
    "semantic_scene_mapping",
    "multi_service_lightbar",
    "state_choreography",
    "integrated_response_shield",
    "native_row_identity_code",
]

STATES = {
    "red": "#ff183f",
    "yellow": "#ffb000",
    "green": "#00d96f",
}
STATE_PALETTES = {
    "red": ("#ff183f", "#8a0f25", "#ff758a"),
    "yellow": ("#ffb000", "#8f5900", "#ffe06a"),
    "green": ("#00d96f", "#08713f", "#7affbc"),
}

INK = "#02070d"
STEEL = "#9bb7cf"
STEEL_DARK = "#26394c"
WHITE = "#f8fbff"

SERVICE_COLOURS = {
    "fire": "#ff4d24",
    "ambulance": "#18e28c",
    "police": "#218cff",
    "marine": "#1ee8ff",
    "mountain": "#f3f4f6",
    "air": "#a78bfa",
    "rail": "#facc15",
    "hazmat": "#d8ff36",
    "mixed": "#b8c7d9",
}

FAMILY_CHASSIS = {
    "fire": "ember_crown",
    "collision": "road_octagon",
    "medical": "clinical_capsule",
    "cardiac": "clinical_capsule",
    "police": "command_shield",
    "crime": "command_shield",
    "marine": "wave_keel",
    "aircraft": "wing_frame",
    "rail": "track_frame",
    "hazmat": "containment_hex",
    "eod": "containment_hex",
    "mountain": "ridge_frame",
    "rescue": "ridge_frame",
    "collapse": "fracture_frame",
    "weather": "storm_arch",
    "utilities": "utility_diamond",
    "animal": "response_roundel",
    "crowd": "response_roundel",
    "response": "response_roundel",
}

SCENE_ROOT = Path(__file__).resolve().parents[1] / "assets" / "scenes"


def chassis_for(family: str) -> str:
    return FAMILY_CHASSIS.get(family, "response_roundel")


def scene_code_for(name: str, slot_id: str) -> str:
    payload = f"{slot_id}|{name}".encode("utf-8")
    return hashlib.blake2s(payload, digest_size=3).hexdigest().upper()


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        size,
    )


def _scene_filename(signature: str) -> str:
    return re.sub(r"[^a-z0-9]+", "--", signature.lower()).strip("-") + ".png"


def _polygon(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    fill: str,
    outline: str | None = INK,
    width: int = 2,
) -> None:
    draw.polygon(points, fill=fill)
    if outline:
        draw.line([*points, points[0]], fill=outline, width=width, joint="curve")


def _centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str = WHITE,
    stroke: str = INK,
    stroke_width: int = 1,
) -> None:
    left, top, right, bottom = box
    bounds = draw.textbbox((0, 0), text, font=text_font, stroke_width=stroke_width)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    draw.text(
        ((left + right - width) / 2, (top + bottom - height) / 2 - bounds[1]),
        text,
        font=text_font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke,
    )


@dataclass(frozen=True)
class IconSpec:
    family: str
    level: int
    services: tuple[str, ...]
    scene_code: str
    signature: str


def _load_scene(signature: str) -> Image.Image:
    path = SCENE_ROOT / _scene_filename(signature)
    if not path.exists():
        raise FileNotFoundError(
            f"No V4 scene master for {signature!r}: {path.relative_to(SCENE_ROOT.parent.parent)}"
        )
    scene = Image.open(path).convert("RGBA")
    return scene.resize((64, 64), Image.Resampling.LANCZOS)


def _render_master(spec: IconSpec, state: str) -> Image.Image:
    colour, dark, light = STATE_PALETTES[state]
    image = Image.new("RGBA", (MASTER_WIDTH, MASTER_HEIGHT), (0, 0, 0, 0))

    aura = Image.new("RGBA", image.size, (0, 0, 0, 0))
    aura_draw = ImageDraw.Draw(aura)
    aura_draw.ellipse((8, 13, 88, 96), fill=(*ImageColor.getrgb(colour), 120))
    image.alpha_composite(aura.filter(ImageFilter.GaussianBlur(6)))
    draw = ImageDraw.Draw(image)

    # Map pointer behind the badge.
    _polygon(draw, [(34, 78), (62, 78), (48, 117)], INK, STEEL_DARK, 3)
    _polygon(draw, [(38, 80), (58, 80), (48, 112)], dark, colour, 3)
    draw.line([(43, 83), (48, 104), (53, 83)], fill=light, width=1)

    # Multi-layer incident aperture.
    draw.ellipse((7, 18, 89, 100), fill=INK)
    draw.ellipse((10, 21, 86, 97), fill=colour)
    draw.ellipse((13, 24, 83, 94), fill=STEEL_DARK)
    draw.ellipse((15, 26, 81, 92), fill=INK)
    image.alpha_composite(_load_scene(spec.signature), (16, 27))
    draw = ImageDraw.Draw(image)
    draw.arc((10, 21, 86, 97), 196, 344, fill=light, width=2)
    draw.arc((10, 21, 86, 97), 16, 164, fill=dark, width=2)

    # Beacon and radio arcs.
    _polygon(draw, [(31, 22), (35, 14), (61, 14), (65, 22), (60, 28), (36, 28)], STEEL_DARK, INK, 3)
    draw.rectangle((37, 15, 59, 21), fill="#41627f")
    draw.rectangle((40, 10, 56, 18), fill=INK)
    draw.rounded_rectangle((42, 5, 54, 17), radius=4, fill=colour, outline=INK, width=2)
    draw.rectangle((45, 7, 51, 12), fill=light)
    draw.line([(34, 12), (28, 7), (26, 2)], fill=colour, width=2)
    draw.line([(62, 12), (68, 7), (70, 2)], fill=colour, width=2)
    draw.arc((20, 0, 76, 34), 196, 244, fill=colour, width=2)
    draw.arc((20, 0, 76, 34), 296, 344, fill=colour, width=2)

    # Shape-coded live state.
    if state == "red":
        for x in (2, 82):
            draw.rounded_rectangle((x, 48, x + 12, 70), radius=3, fill=INK, outline=colour, width=2)
            _centered_text(draw, (x, 48, x + 12, 70), "!", _font(13))
    elif state == "yellow":
        for side in ("left", "right"):
            if side == "left":
                points = [(0, 48), (10, 59), (0, 70), (7, 70), (17, 59), (7, 48)]
            else:
                points = [(96, 48), (86, 59), (96, 70), (89, 70), (79, 59), (89, 48)]
            _polygon(draw, points, colour, INK, 2)
            draw.line(points[1:4], fill=light, width=1)
    else:
        draw.line([(4, 48), (4, 70), (11, 70)], fill=colour, width=3)
        draw.line([(92, 48), (92, 70), (85, 70)], fill=colour, width=3)
        draw.ellipse((72, 5, 94, 27), fill=INK)
        draw.ellipse((74, 7, 92, 25), fill=colour, outline=light, width=1)
        draw.line([(79, 16), (83, 20), (89, 11)], fill=WHITE, width=3)

    # Marine missions keep the approved wave ribbon; all others show the real
    # service mix as compact illuminated segments.
    if spec.family == "marine":
        _polygon(
            draw,
            [(13, 84), (27, 86), (37, 82), (47, 86), (60, 80), (80, 84), (77, 97), (17, 97)],
            "#073d72",
            INK,
            3,
        )
        draw.line([(16, 91), (26, 88), (35, 92), (44, 87), (54, 91), (64, 85), (78, 89)], fill="#28efff", width=3)
        draw.line([(23, 94), (31, 92), (39, 95), (48, 90), (58, 94), (69, 89)], fill="#087fc4", width=2)
    else:
        _polygon(draw, [(14, 86), (82, 86), (78, 99), (18, 99)], STEEL_DARK, INK, 3)
        services = tuple(dict.fromkeys(spec.services))[:5] or ("mixed",)
        left, right, gap = 21, 75, 2
        lamp_width = max(5, (right - left - gap * (len(services) - 1)) // len(services))
        for index, service in enumerate(services):
            x = left + index * (lamp_width + gap)
            lamp = SERVICE_COLOURS.get(service, SERVICE_COLOURS["mixed"])
            draw.rounded_rectangle((x, 90, x + lamp_width, 96), radius=2, fill=INK)
            draw.rectangle((x + 1, 91, x + lamp_width - 1, 94), fill=lamp)
            draw.point((x + 2, 92), fill=WHITE)

    # Permanent gameplay burden shield.
    shield = [(37, 91), (48, 86), (59, 91), (58, 106), (48, 114), (38, 106)]
    _polygon(draw, shield, INK, STEEL, 2)
    inner = [(40, 93), (48, 90), (56, 93), (55, 104), (48, 110), (41, 104)]
    _polygon(draw, inner, "#101923", WHITE, 1)
    _centered_text(draw, (40, 90, 56, 109), str(spec.level), _font(14))

    # Subdued identity encoding prevents semantic twins becoming byte-identical.
    try:
        pattern = int(spec.scene_code[:2], 16)
        full_code = int(spec.scene_code[:6], 16)
    except ValueError:
        pattern = 0
        full_code = 0
    positions = ((11, 33), (10, 40), (10, 77), (83, 33), (84, 40), (84, 77))
    for bit, (x, y) in enumerate(positions):
        mark = light if pattern & (1 << bit) else STEEL_DARK
        draw.rectangle((x, y, x + 2, y + 3), fill=mark)
    code_colours = (STEEL_DARK, colour, light, WHITE)
    for index in range(12):
        value = (full_code >> (index * 2)) & 0b11
        x = 36 + index * 2
        draw.rectangle((x, 118, x + 1, 121), fill=code_colours[value])
    return image


def render_icon(
    state: str,
    level: int,
    primary_service: str,
    services: list[str],
    family: str,
    modifier: str,
    subject: str,
    name: str,
    slot_id: str,
) -> Image.Image:
    """Render one native 64×83 V4 status marker."""
    del primary_service
    if state not in STATES:
        raise ValueError(f"Unknown MissionChief state: {state}")
    signature = f"{family}:{modifier}:{subject}"
    spec = IconSpec(
        family=family,
        level=level,
        services=tuple(services),
        scene_code=scene_code_for(name, slot_id),
        signature=signature,
    )
    master = _render_master(spec, state)
    return master.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
