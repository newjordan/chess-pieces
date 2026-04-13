# Chess Pieces Corpus Ruleset

This file is the submission guideline for keeping the corpus clean and scalable.

## 1) Folder naming

- One set per folder: `styles/<style-name>/`
- Use lowercase kebab-case for style names.
- Keep names descriptive and unique (for example: `classic-lowpoly`, `marble-staunton`, `toon-flat`).

## 2) Required files per style

```text
styles/<style-name>/
  models/
    white/{king,queen,rook,bishop,knight,pawn}.glb
    black/{king,queen,rook,bishop,knight,pawn}.glb
  previews/{king,queen,rook,bishop,knight,pawn}.png
  README.md
```

All 12 model files and all 6 preview files are required.

## 3) Model format + orientation

- Format: `.glb` only.
- Pieces should be upright, centered, and game-ready.
- Keep transforms baked/frozen before export.
- Keep naming exact: `king`, `queen`, `rook`, `bishop`, `knight`, `pawn`.

## 4) Style consistency

- All six pieces in a set must clearly belong to the same visual style.
- White and black sides must read as the same style family.
- Avoid mixing drastically different materials or rendering looks in one set.

## 5) Quality expectations

- No broken geometry (no obvious holes, inverted faces, or exploded meshes).
- Clean silhouette and readable piece identity.
- If low-poly, keep topology intentional, not noisy.

## 6) Licensing

- You must have rights to submit the assets.
- Include license in the style `README.md`.
- Preferred licenses: CC0, CC-BY 4.0, or MIT-compatible asset terms.
- Do not submit copyrighted/IP-restricted assets without permission.

## 7) Style README minimum

Each `styles/<style-name>/README.md` must include:

- Style name
- Author/contributor
- License
- Poly count summary (or note where to find it)
- Notes (toolchain, generation method, or intended use)

## 8) Pull request checklist

Before opening a PR:

- [ ] Folder name is valid and unique.
- [ ] All 12 GLBs are present with exact names.
- [ ] All 6 preview PNGs are present with exact names.
- [ ] Style README includes author + license.
- [ ] Models load and piece identities are clear.

## 9) Maintainer policy

Maintainers may request fixes or reject PRs that do not follow this ruleset.
