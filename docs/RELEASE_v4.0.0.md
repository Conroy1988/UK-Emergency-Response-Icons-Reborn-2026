# Operational V4 release notes

Operational V4 is a full visual replacement of all 871 MissionChief UK graphics
rows and all 2,613 red/amber/green state images.

## What changed

- Replaced the rejected compact centre pictograms with 264 curated illustrated
  incident-scene masters.
- Increased native output from 32 × 37 to 64 × 83 so the approved artwork
  remains legible.
- Retained independent map state, TKB Response Level and service-mix signals.
- Added a deterministic native-row identity code so all 2,613 outputs remain
  unique even when related rows share a semantic scene.
- Added hard QA gates for scene-master coverage, colour depth, transparent
  corners, state signal, map visibility and unique PNG streams.

## Coverage

- 1,066 official catalogue records.
- 869 numbered native slots plus Hand-off and Custom Alliance.
- 871 upload rows.
- 2,613 final PNG files.
- 264 semantic scene masters.

## Publication rule

The repository build, GitHub release and live MissionChief pack are reported
independently. V4 is called live only after every MissionChief image has been
replaced and the live pack has been audited against the final manifest.

## Live synchronization checkpoint

The MissionChief pack was fully replaced and audited on 2026-08-21:

- 871/871 live mission rows present.
- 2,613/2,613 red, amber and green images carry fresh server update timestamps.
- 2,613/2,613 live filenames and state paths match the V4 manifest.
- Zero missing, stale or mismatched live images.
- Native slot `867` was corrected from the retired provisional name `Jet ski
  near the coast` to the current live row `Multi Agency Training Exercise
  (Small)` before its V4 images were uploaded.

This live checkpoint does not by itself publish the GitHub release. The latest
downloadable release remains v2.0.1 until the V4 pull request is merged, tagged
and released.
