# Chess Pieces Corpus

A public, modular collection of 3D chess piece sets.

This repo is designed for two audiences:
- **Users** who want ready-to-use chess assets
- **Contributors** who want to submit new styles

## Quick use

1. Open `catalog.json` to discover available styles.
2. Pick a style folder in `styles/<style-id>/`.
3. Use the GLBs in `models/white` and `models/black`.

## Public, modular layout

```text
catalog.json
styles/
  <style-id>/
    style.json
    models/
      white/{king,queen,rook,bishop,knight,pawn}.glb
      black/{king,queen,rook,bishop,knight,pawn}.glb
    previews/{king,queen,rook,bishop,knight,pawn}.png
    mesh_stats.json
    README.md
```

## Why this is modular

- `catalog.json` is the public index of all style modules.
- Each style has `style.json` with stable paths and metadata.
- Consumers can ingest this corpus without scraping folder names.

See `docs/MODULAR_USAGE.md` for integration guidance.

## Submit your set

Please read:
- `CONTRIBUTING.md`
- `RULESET.md`

Then open a PR with your new style module under `styles/`.

## Current styles

- `classic-lowpoly`

## Goal

Build an open, clean, long-term chess style corpus that is easy to consume and easy to extend.
