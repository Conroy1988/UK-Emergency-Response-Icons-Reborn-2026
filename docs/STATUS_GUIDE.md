# Status and signal guide

Operational V2 separates **what the mission is**, **how large its expected
response is**, **which services it needs**, and **what is happening right now**.
This prevents one colour or number from trying to communicate everything.

## The four marker signals

### 1. Incident signature

The central pictogram identifies the incident family, its main action or hazard,
and the subject involved. A coastguard child search, RTC entrapment and breathing
emergency therefore remain visually distinguishable even when they share a
response level.

### 2. TKB Response Level 1–5

The permanent number estimates gameplay response burden:

| Level | Label | Typical meaning |
|---:|---|---|
| 1 | Routine | Planned, welfare, minor or very small response |
| 2 | Standard | Normal single-service emergency or straightforward medical call |
| 3 | Serious | Several units, casualties, specialist capability or multiple services |
| 4 | Major | Large command-led response, complex rescue or significant hazard |
| 5 | Critical | Mass casualty, aircraft, rail, industrial, nuclear or catastrophic incident |

The number is calculated from MissionChief requirements and remains fixed while
the mission progresses. It is a community gameplay aid, not an official UK
emergency-service grade or clinical triage category.

### 3. Service rail

The coloured side rail shows the operational service mix:

| Colour | Service |
|---|---|
| Red-orange | Fire |
| Blue | Police |
| Green | Ambulance |
| Cyan | Marine/coastguard |
| Purple | Mountain rescue |
| Gold | Air |
| Magenta | Rail |
| Lime | Hazmat |

Up to three service colours appear in a stable order. The rail describes who is
required; it does not describe the live mission state.

### 4. MissionChief map state

| State | Visual language | What it tells the player |
|---|---|---|
| Red | Circular alert mark | The mission is new or still needs action/resources |
| Amber | Diamond movement chevrons | A response is assigned or travelling, but required coverage is not complete |
| Green | Circular tick | Required resources are covered/on scene |

MissionChief chooses the state image automatically. Green represents resource
coverage; it does not guarantee that the mission has completed, paid out or
left the map.

## Common combinations

- **Red Level 1:** a small call that still needs attention.
- **Amber Level 4:** a major response is moving but is not yet fully covered.
- **Green Level 5:** a critical-scale incident whose declared requirements are
  covered/on scene; the operation may still be active.

## Repository and pack status terms

| Term | Exact meaning |
|---|---|
| Latest release | The newest published, downloadable and checksummed GitHub package |
| QA passing | Every deterministic catalogue, mapping, PNG, state, colour, signature and visibility check passed |
| Live pack synced | The public MissionChief rows and filenames were compared with the release manifest and matched |
| Upload queue clear | No image files currently need adding or replacing on MissionChief |
| Official slot | A current native MissionChief slot backed by published catalogue data |
| Legacy slot | A native slot retained for complete pack compatibility although it is absent from the current active catalogue |
| Provisional slot | A native row visible in MissionChief before its full official requirements are published; it uses a conservative temporary classification |
| Special row | Hand-off Mission or Custom Alliance Mission, which sits outside the numbered native catalogue |

## What “QA passing” does and does not mean

Passing QA confirms that the repository builds deterministically and that its
declared pack is internally complete. The separate live-pack audit confirms that
MissionChief is actually using the same mission names and filenames. Both checks
are reported because a correct repository and a correctly uploaded live pack are
different things.

Current checkpoint: **v2.0.1, 871 rows, 2,613 images, zero live mismatches and no
pending uploads**.
