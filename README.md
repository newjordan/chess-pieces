# Chess Pieces Corpus

An open, public corpus of chess piece sets organized by style.

If you make 3D chess pieces, please submit a set. We want this repo to become a clean library of reusable styles for games, tools, and experiments.

## Submit your set

1. Fork this repo.
2. Create a new folder: `styles/<your-style-name>/`
3. Add required files (see `RULESET.md`).
4. Open a PR with a short description and preview images.

## Required structure

```text
styles/
  <style-name>/
    models/
      white/{king,queen,rook,bishop,knight,pawn}.glb
      black/{king,queen,rook,bishop,knight,pawn}.glb
    previews/{king,queen,rook,bishop,knight,pawn}.png
    README.md
```

## Current sets

- `classic-lowpoly`

## Rules and quality bar

See `RULESET.md` for naming, file format, quality, and licensing requirements.

## Goal

Build the best community chess set corpus on GitHub, one style at a time.
