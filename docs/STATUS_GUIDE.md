# Status and signal guide

Operational V4 separates what the mission is, how large its expected response
is, which services it needs, and what is happening right now.

## Marker signals

### Illustrated incident scene

The centre illustration combines the incident family, action/hazard and main
subject. A coastguard child search, RTC entrapment, seizure, weapon incident,
derailment and aircraft crash remain visually distinct even when they share a
response level.

### TKB Response Level 1–5

| Level | Label | Typical meaning |
|---:|---|---|
| 1 | Routine | Planned, welfare, minor or very small response |
| 2 | Standard | Normal single-service emergency or straightforward medical call |
| 3 | Serious | Several units, casualties, specialist capability or multiple services |
| 4 | Major | Large command-led response, complex rescue or significant hazard |
| 5 | Critical | Mass casualty, aircraft, rail, industrial, nuclear or catastrophic incident |

The level stays fixed while the mission progresses. It is a gameplay aid, not
an official grade or clinical triage category.

### Service lightbar

The lower segments show who is needed: fire, police, ambulance,
marine/coastguard, mountain rescue, air, rail, hazmat or mixed. They do not show
the live mission state.

### MissionChief map state

| State | Operational choreography | What it tells the player |
|---|---|---|
| Red | Alert pods, exclamation marks and radio arcs | New mission or action/resources required |
| Amber | Directional chevrons | Response assigned or travelling; coverage incomplete |
| Green | Coverage brackets and tick | Required resources covered/on scene |

Green does not guarantee completion, payout or removal from the map.

## Common combinations

- **Red Level 1:** a small call that still needs attention.
- **Amber Level 4:** a major response is moving but not fully covered.
- **Green Level 5:** a critical-scale incident whose requirements are covered;
  the operation may still be active.

## Repository and pack status terms

| Term | Exact meaning |
|---|---|
| Latest public release | Newest published, downloadable and checksummed GitHub package |
| Release candidate | Complete QA-passing build that is not yet represented as published or live |
| QA passing | Deterministic catalogue, mapping, scene, PNG, state, uniqueness and visibility checks all passed |
| GitHub published | Exact commit is merged and its release archive/tag are public |
| Live pack synced | MissionChief rows and images were checked against a named release manifest and matched |
| Upload queue clear | No image files need adding or replacing on MissionChief |
| Upload replacement pending | Live rows exist, but their images still need replacing with a newer approved build |
| Official slot | Current native MissionChief row backed by published catalogue data |
| Legacy slot | Native row retained for compatibility although absent from the active catalogue |
| Provisional slot | Visible native row awaiting complete official metadata; conservatively classified |
| Special row | Hand-off Mission or Custom Alliance Mission outside the numbered catalogue |

## Current checkpoint

- Public GitHub release: **v2.0.1**.
- GitHub Operational V4 publication: **PR #12 open; branch published and CI
  passing**.
- Live MissionChief pack: **Operational V4 synced on 2026-08-21**, 871 rows and
  2,613 images.
- Operational V4 repository build: **complete and QA passing**, 871 rows and
  2,613 generated images backed by 264 scene masters.
- V4 live upload queue: **clear; 0 replacements pending**.
- Live audit: **2,613/2,613 fresh server timestamps, 2,613/2,613 expected
  filenames and state paths, zero mismatches**.

Passing repository QA, a successful live-pack audit and a published GitHub
release are separate facts. The live pack is V4-synced now; v2.0.1 remains the
latest downloadable GitHub release until PR #12 is merged and V4 is tagged.
