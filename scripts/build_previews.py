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


def main() -> None:
    manifest=json.loads((ROOT/"data"/"mission-manifest.json").read_text(encoding="utf-8")); records=manifest["slots"]
    samples=[]
    for level in range(1,6):
        for family in ("fire","collision","medical","crime","marine","aircraft","rail","hazmat","mountain"):
            found=next((r for r in records if r["level"]==level and r["family"]==family),None)
            if found and found not in samples: samples.append(found)
    samples=samples[:30]
    out=ROOT/"assets"/"previews"; out.mkdir(parents=True,exist_ok=True)
    card_w,card_h=190,78; cols=5; rows=(len(samples)+cols-1)//cols
    backgrounds={"light":"#e8edf2","dark":"#17202b","satellite":"#51614b","greyscale":"#757b80"}
    for state in ("red","yellow","green"):
        sheet=Image.new("RGB",(cols*card_w,rows*card_h),"#0c121b"); draw=ImageDraw.Draw(sheet)
        for idx,r in enumerate(samples):
            x=(idx%cols)*card_w; y=(idx//cols)*card_h; bg=list(backgrounds.values())[idx%4]
            draw.rounded_rectangle((x+4,y+4,x+card_w-4,y+card_h-4),radius=10,fill=bg,outline="#ffffff55",width=1)
            icon=Image.open(ROOT/r["files"][state]).convert("RGBA").resize((48,56),Image.Resampling.NEAREST)
            sheet.paste(icon,(x+10,y+10),icon)
            descriptor=(r["family"] if r["modifier"]==r["family"] else f"{r['family']} · {r['modifier']}").upper()
            descriptor=descriptor[:16]+("…" if len(descriptor)>16 else "")
            draw.text((x+66,y+12),f"L{r['level']} · {descriptor}",font=font(10),fill="white",stroke_width=2,stroke_fill="#111827")
            name=r["name"][:25]+("…" if len(r["name"])>25 else "")
            draw.text((x+66,y+34),name,font=font(10),fill="white",stroke_width=2,stroke_fill="#111827")
            draw.text((x+66,y+52),f"SLOT {r['slot_id']}",font=font(9),fill="#dbeafe",stroke_width=2,stroke_fill="#111827")
        sheet.save(out/f"overview-{state}.png",optimize=True)

    lines=["# Complete mission gallery","",f"**{manifest['catalogue_record_count']:,} official records mapped to {manifest['upload_slot_count']:,} native slots · {len(records)*3:,} status graphics**","","[Use this pack on MissionChief](https://www.missionchief.co.uk/mission_graphics/539)",""]
    for level in range(1,6):
        lines.extend([f"## Level {level}","","| Mission slot | Red | Amber | Green | Signature |","|---|---:|---:|---:|---|"])
        for r in (slot for slot in records if slot["level"]==level):
            variants=f" · {r['variant_count']} catalogue variant{'s' if r['variant_count'] != 1 else ''}" if r["source_kind"]=="official" else ""
            lines.append(f"| `{r['slot_id']}` {r['name']}{variants} | ![]({r['files']['red']}) | ![]({r['files']['yellow']}) | ![]({r['files']['green']}) | {r['family']} · {r['modifier']} · {r['subject']} |")
    (ROOT/"GALLERY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__": main()
