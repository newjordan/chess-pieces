# classic-lowpoly

Faceted Staunton-like pieces.

- Module ID: `classic-lowpoly`
- Author: Frosty40
- License: CC BY 4.0
- Format: GLB
- Shading: flat (one vertex per corner, so unique position counts are lower than `vertices`)
- Piece types: king, queen, rook, bishop, knight, pawn
- Sides: white and black share geometry. Each GLB embeds its own PBR material (`white` or `black`)
- Pose: Y-up, base on `y = 0`, footprint centered, asymmetric crowns face −Z
- Poly stats: `mesh_stats.json` (measured from the GLBs)
- Manifest: `style.json`
- `previews/` are 768×768 renders of the white GLBs
- `references/` keeps the original 1024×1024 studio stills

The meshes are low-poly, and some stems do not sit on the vertical center line. The king's neck is the clear case: from height 0.48 to 0.58 its Z extent is −0.177 to −0.077.
