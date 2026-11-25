"""Rewrite style modules and print measured stats."""

from __future__ import annotations

import json
from pathlib import Path

from chesscorpus.gltf import MeshData, read_glb, write_glb
from chesscorpus.layout import PIECES, PREVIEW_SIZE, SIDES
from chesscorpus.materials import MATERIALS
from chesscorpus.mesh import normalize_mesh, published_stats
from chesscorpus.render import render_preview
from chesscorpus.validate import validate_corpus


def normalize_corpus(root: Path) -> None:
    root = Path(root)
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    for entry in catalog["styles"]:
        style_id = entry["id"]
        style_dir = root / "styles" / style_id
        manifest = json.loads((style_dir / "style.json").read_text(encoding="utf-8"))
        shading = manifest["shading"]
        stats: dict[str, dict] = {}
        for piece in PIECES:
            for side in SIDES:
                path = style_dir / manifest["models"][side][piece]
                source = read_glb(path.read_bytes())
                positions, indices, normals = normalize_mesh(
                    source.positions, source.indices, shading=shading
                )
                mesh = MeshData(piece, positions, indices, normals, MATERIALS[side])
                path.write_bytes(write_glb(mesh))
                if side == "white":
                    stats[piece] = published_stats(positions, indices)
                    stat = stats[piece]
                    print(
                        f"{style_id}/{piece}: {stat['vertices']} verts, "
                        f"{stat['faces']} faces, height {stat['height']}, "
                        f"width {stat['width']}, depth {stat['depth']}"
                    )
        destination = style_dir / "mesh_stats.json"
        destination.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")


def render_corpus(root: Path) -> None:
    root = Path(root)
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    for entry in catalog["styles"]:
        style_id = entry["id"]
        style_dir = root / "styles" / style_id
        manifest = json.loads((style_dir / "style.json").read_text(encoding="utf-8"))
        for piece in PIECES:
            path = style_dir / manifest["models"]["white"][piece]
            mesh = read_glb(path.read_bytes())
            preview = style_dir / manifest["previews"][piece]
            preview.parent.mkdir(parents=True, exist_ok=True)
            payload = render_preview(mesh.positions, mesh.indices, size=PREVIEW_SIZE)
            preview.write_bytes(payload)
            print(f"rendered {style_id}/{piece} ({len(payload)} bytes)")


def report_corpus(root: Path) -> str:
    lines = [
        "| Style | Piece | Vertices | Unique | Faces | Height | Width | Depth |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    root = Path(root)
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    for entry in catalog["styles"]:
        stats = json.loads((root / entry["path"] / "mesh_stats.json").read_text(encoding="utf-8"))
        for piece in PIECES:
            row = stats[piece]
            lines.append(
                f"| {entry['id']} | {piece} | {row['vertices']} | {row['uniquePositions']} | "
                f"{row['faces']} | {row['height']} | {row['width']} | {row['depth']} |"
            )
    return "\n".join(lines)


def validation_errors(root: Path) -> list[str]:
    return validate_corpus(root)
