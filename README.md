# Chess Pieces

A collection of chess piece sets organized by style.

## Styles

- `classic-lowpoly` (current set)

## Structure

```text
styles/
  <style-name>/
    models/
      white/{king,queen,rook,bishop,knight,pawn}.glb
      black/{king,queen,rook,bishop,knight,pawn}.glb
    previews/{king,queen,rook,bishop,knight,pawn}.png
    mesh_stats.json
```

## Add a new style set

1. Create `styles/<new-style-name>/`
2. Add `models/white` and `models/black` GLBs for all 6 piece types.
3. Add preview PNGs and optional `mesh_stats.json`.
4. Commit and push.

