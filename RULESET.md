# Chess Pieces Corpus Ruleset

This ruleset keeps the repository public-friendly and modular at scale.

## 1) Style module naming

- One style per folder: `styles/<style-id>/`
- `<style-id>` must be lowercase kebab-case and unique.

## 2) Required files per style module

```text
styles/<style-id>/
  style.json
  models/
    white/{king,queen,rook,bishop,knight,pawn}.glb
    black/{king,queen,rook,bishop,knight,pawn}.glb
  previews/{king,queen,rook,bishop,knight,pawn}.png
  README.md
```

Optional but recommended:
- `mesh_stats.json`

## 3) Required global index update

Every new style PR must update `catalog.json` with:
- `id`
- `name`
- `version`
- `path`
- `styleManifest`
- `license`
- `pieceFormat`

## 4) `style.json` minimum schema

Each style manifest must include:
- `id`, `name`, `version`
- `author`, `license`, `format`
- `pieces`
- `models.white.*` and `models.black.*`
- `previews.*`

Paths in `style.json` must be relative to the style folder.

## 5) Asset format and naming

- Model format: `.glb` only
- Piece names must be exact:
  - `king`, `queen`, `rook`, `bishop`, `knight`, `pawn`
- All pieces must be upright and game-ready.

## 6) Style consistency

- A style set must read as one coherent visual family.
- White and black must be same style family.
- Piece identities must be clearly recognizable.

## 7) Quality floor

Rejectable issues include:
- Broken meshes (holes, inverted normals, severe artifacts)
- Missing required files
- Ambiguous piece identity
- Inconsistent naming/paths

## 8) Licensing and rights

- Submit only assets you have the right to publish.
- Include license in style `README.md` and `style.json`.
- Recommended: CC0, CC-BY 4.0, or permissive terms.

## 9) PR checklist

- [ ] New style folder uses valid `style-id`
- [ ] `style.json` complete and paths valid
- [ ] 12 GLBs present (6 white + 6 black)
- [ ] 6 previews present
- [ ] `catalog.json` updated
- [ ] Style README includes author/license/notes

Maintainers may request changes or reject submissions that do not follow this ruleset.
