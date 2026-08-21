#!/usr/bin/env python3
"""Create representative pack previews and a browsable Markdown gallery."""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]


def font(size: int):
    path=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default()


def fit_text(draw: ImageDraw.ImageDraw, value: str, max_width: int, start_size: int=18):
    size=start_size
    while size>9:
        candidate=font(size)
        if draw.textbbox((0,0),value,font=candidate)[2] <= max_width:
            return candidate
        size-=1
    return font(9)


def build_showcase(records: list[dict], out: Path) -> None:
    """Build a human-review sheet of V4 triptychs across the incident families."""
    targets=(
        "Lost Child at Beach - Coastguard Search",
        "RTC Entrapment",
        "House fire (Persons Reported)",
        "Seizure",
        "Person with a weapon",
        "Large Aircraft Crash Off Airport",
        "Passenger Train Derailment",
        "Large fuel spill in petrol station forecourt",
        "Person Stuck on Cliff",
        "Domestic drowning",
        "Prison Wing Fire (Persons Reported)",
        "Road Traffic Collision (Major)",
    )
    chosen=[]
    for target in targets:
        found=next((record for record in records if record["name"].casefold()==target.casefold()),None)
        if found and found not in chosen:
            chosen.append(found)
    cols=3; card_w=420; card_h=236; rows=(len(chosen)+cols-1)//cols
    sheet=Image.new("RGB",(cols*card_w,rows*card_h+64),"#070b11")
    draw=ImageDraw.Draw(sheet)
    draw.text((24,14),"OPERATIONAL V4 · PREMIUM INCIDENT-SCENE AUDIT",font=font(24),fill="white")
    draw.text((24,42),"RED · INBOUND · COVERED  |  native 64×83 illustrated markers",font=font(12),fill="#9fb3c8")
    for index,record in enumerate(chosen):
        x=(index%cols)*card_w; y=64+(index//cols)*card_h
        draw.rounded_rectangle((x+7,y+7,x+card_w-7,y+card_h-7),radius=14,fill="#111b27",outline="#314358",width=2)
        label=record["name"]
        draw.text((x+18,y+15),label,font=fit_text(draw,label,card_w-36),fill="white")
        detail=f"L{record['level']} · {record['family']} / {record['modifier']} / {record['subject']} · {record['scene_code']}"
        draw.text((x+18,y+39),detail.upper(),font=font(9),fill="#8dd7ff")
        for state_index,state in enumerate(("red","yellow","green")):
            icon=Image.open(ROOT/record["files"][state]).convert("RGBA").resize((96,124),Image.Resampling.LANCZOS)
            ix=x+25+state_index*128; iy=y+62
            draw.rounded_rectangle((ix-6,iy-5,ix+102,iy+151),radius=9,fill=("#25131a" if state=="red" else "#241e10" if state=="yellow" else "#10231b"))
            sheet.paste(icon,(ix,iy),icon)
            label="AMBER" if state=="yellow" else state.upper()
            draw.text((ix+48,iy+132),label,font=font(9),anchor="ma",fill="#dce8f5")
    sheet.save(out/"v4-incident-scene-audit.png",optimize=True)


def build_dense_map_audit(records: list[dict], out: Path) -> None:
    """Render real 50% markers on the four backgrounds used by QA."""
    backgrounds=(
        ("LIGHT",(232,237,242)),
        ("DARK",(23,32,43)),
        ("SATELLITE",(81,97,75)),
        ("GREYSCALE",(117,123,128)),
    )
    cols=14; cell_w=39; row_h=49; margin=62; header=24
    base=Image.new("RGB",(margin+cols*cell_w+8,header+len(backgrounds)*row_h+8),"#070b11")
    draw=ImageDraw.Draw(base)
    draw.text((6,5),"V4 · TRUE 50% MAP SCALE",font=font(9),fill="white")
    for row,(label,background) in enumerate(backgrounds):
        y=header+row*row_h
        draw.rectangle((0,y,base.width,y+row_h),fill=background)
        draw.text((5,y+9),label,font=font(6),fill="white",stroke_width=1,stroke_fill="#07111a")
        for col in range(cols):
            record=records[(row*cols+col)*11 % len(records)]
            state=("red","yellow","green")[(row+col)%3]
            icon=Image.open(ROOT/record["files"][state]).convert("RGBA").resize((32,42),Image.Resampling.LANCZOS)
            base.paste(icon,(margin+col*cell_w,y+4),icon)
    enlarged=base.resize((base.width*2,base.height*2),Image.Resampling.NEAREST)
    enlarged.save(out/"v4-dense-map-audit.png",optimize=True)


def main() -> None:
    manifest=json.loads((ROOT/"data"/"mission-manifest.json").read_text(encoding="utf-8")); records=manifest["slots"]
    samples=[]
    for level in range(1,6):
        for family in ("fire","collision","medical","crime","marine","aircraft","rail","hazmat","mountain"):
            found=next((r for r in records if r["level"]==level and r["family"]==family),None)
            if found and found not in samples: samples.append(found)
    samples=samples[:30]
    out=ROOT/"assets"/"previews"; out.mkdir(parents=True,exist_ok=True)
    card_w,card_h=240,108; cols=4; rows=(len(samples)+cols-1)//cols
    backgrounds={"light":"#e8edf2","dark":"#17202b","satellite":"#51614b","greyscale":"#757b80"}
    for state in ("red","yellow","green"):
        sheet=Image.new("RGB",(cols*card_w,rows*card_h),"#0c121b"); draw=ImageDraw.Draw(sheet)
        for idx,r in enumerate(samples):
            x=(idx%cols)*card_w; y=(idx//cols)*card_h; bg=list(backgrounds.values())[idx%4]
            draw.rounded_rectangle((x+4,y+4,x+card_w-4,y+card_h-4),radius=10,fill=bg,outline="#ffffff55",width=1)
            icon=Image.open(ROOT/r["files"][state]).convert("RGBA")
            sheet.paste(icon,(x+10,y+10),icon)
            descriptor=(r["family"] if r["modifier"]==r["family"] else f"{r['family']} · {r['modifier']}").upper()
            descriptor=descriptor[:16]+("…" if len(descriptor)>16 else "")
            draw.text((x+82,y+12),f"L{r['level']} · {descriptor}",font=font(10),fill="white",stroke_width=2,stroke_fill="#111827")
            name=r["name"][:25]+("…" if len(r["name"])>25 else "")
            draw.text((x+82,y+40),name,font=font(10),fill="white",stroke_width=2,stroke_fill="#111827")
            draw.text((x+82,y+68),f"SLOT {r['slot_id']}",font=font(9),fill="#dbeafe",stroke_width=2,stroke_fill="#111827")
        sheet.save(out/f"overview-{state}.png",optimize=True)

    build_showcase(records,out)
    build_dense_map_audit(records,out)

    lines=["# Complete mission gallery","",f"**{manifest['catalogue_record_count']:,} official records mapped to {manifest['upload_slot_count']:,} native slots · {len(records)*3:,} status graphics**","","[Use this pack on MissionChief](https://www.missionchief.co.uk/mission_graphics/539)",""]
    for level in range(1,6):
        lines.extend([f"## Level {level}","","| Mission slot | Red | Amber | Green | Signature |","|---|---:|---:|---:|---|"])
        for r in (slot for slot in records if slot["level"]==level):
            variants=f" · {r['variant_count']} catalogue variant{'s' if r['variant_count'] != 1 else ''}" if r["source_kind"]=="official" else ""
            lines.append(f"| `{r['slot_id']}` {r['name']}{variants} | ![]({r['files']['red']}) | ![]({r['files']['yellow']}) | ![]({r['files']['green']}) | {r['family']} · {r['modifier']} · {r['subject']} |")
    (ROOT/"GALLERY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__": main()
