# Operational V2 icon system

Operational V2 is a deterministic visual grammar for MissionChief UK. It keeps
the complete pack coherent while giving individual incidents a recognisable
mission signature at the game's native marker size.

## Fixed delivery contract

- Canvas: 32 × 37 pixels, transparent RGBA.
- Body: dark operational map pin with a dual light/status keyline.
- Output: one red, amber and green PNG for every upload slot.
- Source: every pixel is generated from code. No external logos, registrations
  or copied artwork are embedded.

## Visual layers

1. **Incident family** establishes the primary silhouette: fire, medical,
   collision, marine, aircraft, rail, hazmat, rescue and the remaining
   deterministic families.
2. **Semantic modifier** identifies the operational action or condition, such
   as search, entrapment, persons reported, theft, weapons, breathing,
   neurological injury, flooding or chemical release.
3. **Contextual subject** identifies what is involved, such as a child,
   hospital, school, HGV, vessel, aircraft, home, industrial site, crowd,
   animal or infrastructure.
4. **Multi-service rail** displays up to three required services in a stable
   vertical order. A mixed mission no longer collapses into an uninformative
   white strip.
5. **Response shield** permanently displays TKB Response Level 1–5.
6. **State shell** communicates live MissionChief progress through both colour
   and shape.

## State language

- Red `#ff4357`: circular alert mark — new mission or action required.
- Amber `#ffc145`: diamond movement chevrons — response under way.
- Green `#32d583`: circular tick — required resources covered/on scene.

The coloured tail and lower band remain familiar to existing pack users, while
the full status keyline improves detection on busy maps.

## Service colours

- Fire `#ff5a47`
- Police `#4ca6ff`
- Ambulance `#29d391`
- Marine `#22c7d9`
- Mountain rescue `#b88cff`
- Air `#ffcf5a`
- Rail `#e067ff`
- Hazmat `#c6ef4e`

## Complexity limits

- One dominant incident silhouette.
- One semantic modifier and one contextual subject.
- No more than three service-rail segments.
- No text other than the single response-level numeral.
- Optical review always occurs at 32 × 37 and the simulated 16 × 19 half-map
  size, not only on enlarged previews.

The manifest records the family, modifier, subject and complete signature for
every official record and native slot. Identical inputs always rebuild to
identical PNG bytes.
