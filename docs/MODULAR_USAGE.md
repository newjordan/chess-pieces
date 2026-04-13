# Modular Usage Guide

This corpus is designed to be consumed as modules.

## Discover available styles

Read `catalog.json`.

Each style entry points to `styles/<style-id>/style.json`.

## Load one style module

1. Read `style.json`
2. Resolve model paths from `models.white.*` / `models.black.*`
3. Resolve previews from `previews.*`
4. Optionally read `meshStats`

## Contract stability

For each style module:
- Piece keys remain: `king`, `queen`, `rook`, `bishop`, `knight`, `pawn`
- Model format remains `.glb`
- Relative paths are stable inside that style folder

## Example consumer workflow

- Select style ID from `catalog.json`
- Read style manifest
- Load white/black GLBs into engine
- Assign side materials in runtime

This allows tools to swap style sets without changing code paths.
