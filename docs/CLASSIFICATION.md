# TKB Response Levels

The permanent number on each marker is a gameplay-oriented estimate of the
mission's response burden. It is not an official UK emergency-service grade.

| Level | Meaning | Typical profile |
|---|---|---|
| 1 | Routine | Planned, minor, welfare or very small single-resource incident |
| 2 | Standard | Small single-service emergency or straightforward medical call |
| 3 | Serious | Several units, specialist capability, casualties or multiple services |
| 4 | Major | Large command-led response, complex rescue or significant hazard |
| 5 | Critical | Mass casualty, aircraft, rail, industrial, nuclear or catastrophic incident |

## Deterministic inputs

The classifier combines:

- guaranteed vehicle and personnel requirements;
- specialist, command, air, marine, rail and hazardous-material capability;
- the number of emergency services involved;
- potential patients, transport probability and critical-care probability;
- official UK ambulance acuity codes, with bounded weight for C1–C4 calls;
- declared major/alliance status and severe incident language;
- average credits as a bounded supporting signal.

Every output includes its raw score and component breakdown in
`data/mission-manifest.json`. The thresholds are versioned in
`data/classifier-profile.json` so a mission never changes level silently.

MissionChief exposes one graphics slot per base mission, while its catalogue
contains additive variants. Every official record is classified independently;
the native slot displays the highest level among its current variants. This
prevents an escalated variant from appearing less serious than its base call.

## Operational V2 signature classification

Response level and visual identity remain separate deterministic decisions.
After the level is calculated, Operational V2 derives three visual layers from
the canonical mission title and classified service data:

- incident family for the dominant silhouette;
- semantic modifier for the action, hazard or clinical condition;
- contextual subject for the person, vehicle, premises, environment or
  infrastructure involved.

Required services populate the segmented service rail independently of those
three layers. The complete values are stored for every record and upload slot in
`data/mission-manifest.json`, making visual changes auditable alongside level
changes.
