# Modular Usage Guide

Load a style from `catalog.json` and `style.json`. Do not scrape folder names.

## Discover styles

`catalog.json` is schema 1.1.0. Each entry has `id`, `path`, `styleManifest`, `license`, `shading`, and `pieceFormat`.

```text
catalog.json
  -> styles/<style-id>/style.json
       -> models/white/<piece>.glb
       -> models/black/<piece>.glb
       -> previews/<piece>.png
       -> mesh_stats.json
```

Piece keys are `king`, `queen`, `rook`, `bishop`, `knight`, `pawn`. Model files are glTF 2.0 `.glb`.

## Pose and materials

Every mesh in the catalog uses one pose:

- Y is up and is the longest side of the bounding box
- the base sits on `y = 0`
- the XZ footprint is centered
- an asymmetric crown faces −Z
- normals are unit length and triangles wind outward

White and black files for a piece share positions and indices. The embedded material name is `white` or `black`. Replace that material in your engine if you want a different palette. `shading` is `flat` or `smooth`: flat files store one vertex per corner, smooth files share vertices.

`mesh_stats.json` reports `vertices`, `faces`, `uniquePositions`, `height`, `width`, and `depth` measured from the white file. Height is the Y extent.

## Example

From the repo root, with the package installed:

```python
import json
from pathlib import Path

from chesscorpus.gltf import read_glb

root = Path(".")
catalog = json.loads((root / "catalog.json").read_text())
entry = next(style for style in catalog["styles"] if style["id"] == "classic-lowpoly")
manifest = json.loads((root / entry["styleManifest"]).read_text())
king = root / entry["path"] / manifest["models"]["white"]["king"]
mesh = read_glb(king.read_bytes())
print(mesh.name, len(mesh.positions), len(mesh.indices), mesh.material.name)
```

A three.js client can fetch the same relative URL. The gallery in `preview/` does that: `chesscorpus preview`, then <http://127.0.0.1:8000/preview/>.

`references/` inside a style is source art. It is not listed in `style.json` and is not part of the load contract.
