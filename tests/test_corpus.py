"""The checked-in corpus, plus a synthetic module that must fail validation."""

import json
from pathlib import Path

import numpy as np

from chesscorpus.__main__ import main
from chesscorpus.gltf import MeshData, write_glb
from chesscorpus.layout import ORIENTATION, SCHEMA_VERSION
from chesscorpus.materials import WHITE
from chesscorpus.validate import validate_corpus

ROOT = Path(__file__).resolve().parents[1]

# Face counts measured from the authored meshes. Topology is not rebuilt.
EXPECTED_FACES = {
    "classic-lowpoly": {
        "king": 1496,
        "queen": 1584,
        "rook": 2000,
        "bishop": 1968,
        "knight": 2796,
        "pawn": 2324,
    },
    "ai-triposr-v1": {
        "king": 64612,
        "queen": 89656,
        "rook": 82368,
        "bishop": 60532,
        "knight": 142020,
        "pawn": 72136,
    },
}


def test_repository_matches_the_contract():
    errors = validate_corpus(ROOT)
    assert errors == []
    assert main(["--root", str(ROOT), "validate"]) == 0


def test_published_face_counts_are_unchanged():
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    for entry in catalog["styles"]:
        stats = json.loads((ROOT / entry["path"] / "mesh_stats.json").read_text(encoding="utf-8"))
        for piece, faces in EXPECTED_FACES[entry["id"]].items():
            assert stats[piece]["faces"] == faces
        if entry["shading"] == "flat":
            for piece, row in stats.items():
                assert row["vertices"] == row["faces"] * 3


def test_sideways_module_is_rejected(tmp_path: Path):
    style = tmp_path / "styles" / "sample-set"
    for side in ("white", "black"):
        (style / "models" / side).mkdir(parents=True)
    (style / "previews").mkdir()
    positions = np.array(
        [[-1.0, -0.2, -0.2], [-1.0, 0.2, -0.2], [-1.0, 0.0, 0.3], [1.0, 0.0, 0.0]],
        dtype=np.float32,
    )
    indices = np.array([[0, 1, 3], [1, 2, 3], [2, 0, 3], [0, 2, 1]], dtype=np.int64)
    normals = np.zeros_like(positions)
    normals[:, 0] = 1
    payload = write_glb(MeshData("king", positions, indices, normals, WHITE))
    for piece in ("king", "queen", "rook", "bishop", "knight", "pawn"):
        for side in ("white", "black"):
            (style / "models" / side / f"{piece}.glb").write_bytes(payload)
        _write_preview(style / "previews" / f"{piece}.png")
    manifest = {
        "id": "sample-set",
        "name": "Sample",
        "version": "1.0.0",
        "author": "Test",
        "license": "CC-BY 4.0",
        "format": "glb",
        "shading": "smooth",
        "orientation": ORIENTATION,
        "pieces": ["king", "queen", "rook", "bishop", "knight", "pawn"],
        "models": {
            side: {piece: f"models/{side}/{piece}.glb" for piece in manifest_pieces()}
            for side in ("white", "black")
        },
        "previews": {piece: f"previews/{piece}.png" for piece in manifest_pieces()},
        "meshStats": "mesh_stats.json",
    }
    (style / "style.json").write_text(json.dumps(manifest), encoding="utf-8")
    (style / "mesh_stats.json").write_text("{}", encoding="utf-8")
    (style / "README.md").write_text("sample\n", encoding="utf-8")
    catalog = {
        "schemaVersion": SCHEMA_VERSION,
        "styles": [
            {
                "id": "sample-set",
                "name": "Sample",
                "version": "1.0.0",
                "path": "styles/sample-set",
                "styleManifest": "styles/sample-set/style.json",
                "license": "CC-BY 4.0",
                "shading": "smooth",
                "pieceFormat": "glb",
            }
        ],
    }
    (tmp_path / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    errors = validate_corpus(tmp_path)
    assert any("not upright" in error for error in errors)
    assert main(["--root", str(tmp_path), "validate"]) == 1


def test_missing_catalog_is_an_error(tmp_path: Path):
    errors = validate_corpus(tmp_path)
    assert errors
    assert "catalog.json" in errors[0]


def manifest_pieces() -> tuple[str, ...]:
    return ("king", "queen", "rook", "bishop", "knight", "pawn")


def _write_preview(path: Path) -> None:
    from PIL import Image

    image = Image.new("RGB", (768, 768), (180, 176, 170))
    for x in range(768):
        image.putpixel((x, x), (240, 230, 210))
    image.save(path, format="PNG")
