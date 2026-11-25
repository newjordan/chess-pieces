"""Check a corpus checkout against the public module contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from chesscorpus.gltf import read_glb
from chesscorpus.layout import ORIENTATION, PIECES, PREVIEW_SIZE, SCHEMA_VERSION, SHADING, SIDES
from chesscorpus.materials import luminance
from chesscorpus.mesh import mesh_metrics, published_stats

_STYLE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PREVIEW_BYTES = 400_000


def validate_corpus(root: Path) -> list[str]:
    root = Path(root)
    errors: list[str] = []
    catalog_path = root / "catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"catalog.json: {exc}"]

    if catalog.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(
            f"catalog.json: schemaVersion must be {SCHEMA_VERSION} "
            f"(found {catalog.get('schemaVersion')!r})"
        )
    styles = catalog.get("styles")
    if not isinstance(styles, list) or not styles:
        return [*errors, "catalog.json: styles must be a non-empty list"]

    seen: set[str] = set()
    for entry in styles:
        errors.extend(_validate_style(root, entry, seen))
    return errors


def _validate_style(root: Path, entry: object, seen: set[str]) -> list[str]:
    if not isinstance(entry, dict):
        return ["catalog.json: style entry is not an object"]
    style_id = entry.get("id")
    errors: list[str] = []
    label = f"catalog style {style_id!r}"
    if not isinstance(style_id, str) or not _STYLE_ID.match(style_id):
        return [f"{label}: id must be lowercase kebab-case"]
    if style_id in seen:
        errors.append(f"{label}: duplicate id")
    seen.add(style_id)

    relative = entry.get("path")
    manifest_path = entry.get("styleManifest")
    if relative != f"styles/{style_id}":
        errors.append(f"{label}: path must be styles/{style_id}")
    if manifest_path != f"styles/{style_id}/style.json":
        errors.append(f"{label}: styleManifest must be styles/{style_id}/style.json")
    if entry.get("pieceFormat") != "glb":
        errors.append(f"{label}: pieceFormat must be 'glb'")
    shading = entry.get("shading")
    if shading not in SHADING:
        errors.append(f"{label}: shading must be one of {', '.join(SHADING)}")

    style_dir = root / "styles" / style_id
    manifest_file = style_dir / "style.json"
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [*errors, f"{style_id}/style.json: {exc}"]

    if manifest.get("id") != style_id:
        errors.append(f"{style_id}: style.json id does not match the folder")
    if manifest.get("license") != entry.get("license"):
        errors.append(f"{style_id}: catalog license does not match style.json")
    if manifest.get("shading") != shading:
        errors.append(f"{style_id}: catalog shading does not match style.json")
    if manifest.get("orientation") != ORIENTATION:
        errors.append(f"{style_id}: orientation must be {ORIENTATION}")
    if manifest.get("format") != "glb":
        errors.append(f"{style_id}: format must be 'glb'")
    declared = manifest.get("pieces")
    if sorted(declared or []) != sorted(PIECES):
        errors.append(f"{style_id}: pieces must be {', '.join(PIECES)}")

    models = manifest.get("models") or {}
    previews = manifest.get("previews") or {}
    loaded: dict[tuple[str, str], object] = {}
    for side in SIDES:
        for piece in PIECES:
            pointer = (models.get(side) or {}).get(piece)
            errors.extend(_check_relative(style_dir, pointer, f"{style_id} models.{side}.{piece}"))
            model_path = _resolve(style_dir, pointer)
            if model_path is None or not model_path.is_file():
                continue
            try:
                loaded[(side, piece)] = read_glb(model_path.read_bytes())
            except (OSError, ValueError, KeyError) as exc:
                errors.append(f"{model_path.relative_to(style_dir.parent.parent)}: {exc}")

    for piece in PIECES:
        pointer = previews.get(piece)
        errors.extend(_check_relative(style_dir, pointer, f"{style_id} previews.{piece}"))
        preview_path = _resolve(style_dir, pointer)
        if preview_path is not None and preview_path.is_file():
            errors.extend(_check_preview(preview_path))

    stats_path = style_dir / "mesh_stats.json"
    try:
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{style_id}/mesh_stats.json: {exc}")
        stats = {}
    if manifest.get("meshStats") != "mesh_stats.json":
        errors.append(f"{style_id}: meshStats must be mesh_stats.json")
    if not (style_dir / "README.md").is_file():
        errors.append(f"{style_id}: README.md is missing")

    for piece in PIECES:
        white = loaded.get(("white", piece))
        black = loaded.get(("black", piece))
        if white is None or black is None:
            continue
        errors.extend(_check_pair(style_id, piece, shading, white, black, stats.get(piece)))
    return errors


def _resolve(style_dir: Path, pointer: object) -> Path | None:
    if not isinstance(pointer, str) or pointer == "":
        return None
    return (style_dir / pointer).resolve()


def _check_relative(style_dir: Path, pointer: object, label: str) -> list[str]:
    if not isinstance(pointer, str) or pointer == "" or Path(pointer).is_absolute():
        return [f"{label}: path must be a relative string"]
    if ".." in Path(pointer).parts:
        return [f"{label}: path must stay inside the style folder"]
    resolved = (style_dir / pointer).resolve()
    if not resolved.is_relative_to(style_dir.resolve()):
        return [f"{label}: path escapes the style folder"]
    if not resolved.is_file():
        return [f"{label}: missing file {pointer}"]
    return []


def _check_preview(path: Path) -> list[str]:
    errors: list[str] = []
    if path.stat().st_size > _PREVIEW_BYTES:
        errors.append(f"{path.name}: preview is {path.stat().st_size} bytes, over {_PREVIEW_BYTES}")
    try:
        with Image.open(path) as image:
            image.load()
            size_ok = image.size == (PREVIEW_SIZE, PREVIEW_SIZE)
            if image.format != "PNG" or not size_ok or image.mode != "RGB":
                errors.append(
                    f"{path.name}: preview must be {PREVIEW_SIZE}x{PREVIEW_SIZE} RGB PNG "
                    f"(found {image.format} {image.size} {image.mode})"
                )
                return errors
            pixels = np.asarray(image)
    except OSError as exc:
        return [f"{path.name}: {exc}"]
    if float(pixels.std()) < 8.0:
        errors.append(f"{path.name}: preview looks blank")
    return errors


def _check_pair(style_id, piece, shading, white, black, stats) -> list[str]:
    errors: list[str] = []
    prefix = f"{style_id}/{piece}"
    if white.normals is None or black.normals is None:
        errors.append(f"{prefix}: normals are missing")
        return errors
    if not np.array_equal(white.positions, black.positions) or not np.array_equal(
        white.indices, black.indices
    ):
        errors.append(f"{prefix}: white and black geometry differ")
    for side, mesh in ("white", white), ("black", black):
        if mesh.material is None or mesh.material.name != side:
            errors.append(f"{prefix}: {side} material is missing or misnamed")
            continue
        glow = luminance(mesh.material.base_color)
        if side == "white" and glow < 0.4:
            errors.append(f"{prefix}: white material is too dark ({glow:.3f})")
        if side == "black" and glow > 0.08:
            errors.append(f"{prefix}: black material is too light ({glow:.3f})")
        errors.extend(_check_geometry(f"{prefix}/{side}", mesh, shading))
    if stats is None:
        errors.append(f"{prefix}: mesh_stats.json has no entry")
    else:
        measured = published_stats(white.positions, white.indices)
        for key, value in measured.items():
            if stats.get(key) != value:
                errors.append(
                    f"{prefix}: mesh_stats {key} is {stats.get(key)!r}, measured {value!r}"
                )
    return errors


def _check_geometry(label: str, mesh, shading: str | None) -> list[str]:
    errors: list[str] = []
    metrics = mesh_metrics(mesh.positions, mesh.indices)
    if abs(float(metrics["min"][1])) > 1e-4:
        errors.append(f"{label}: base is not on y=0 (min y = {float(metrics['min'][1]):.5f})")
    center = metrics["center"]
    if abs(float(center[0])) > 1e-3 or abs(float(center[2])) > 1e-3:
        errors.append(f"{label}: footprint is not centered on x/z")
    span = metrics["span"]
    if float(span[1]) + 1e-4 < max(float(span[0]), float(span[2])):
        errors.append(f"{label}: mesh is not upright (span {span.round(4).tolist()})")
    if metrics["outward"] < 0.5:
        errors.append(f"{label}: winding faces inward ({metrics['outward']:.2f} outward)")
    lengths = np.linalg.norm(np.asarray(mesh.normals, dtype=np.float64), axis=1)
    if not np.isfinite(lengths).all() or float(lengths.mean()) < 0.99:
        errors.append(f"{label}: normals are missing or not unit length")
    if shading == "flat":
        if metrics["vertices"] != metrics["faces"] * 3:
            errors.append(f"{label}: flat shading must store one vertex per corner")
        corners = mesh.indices
        normals = np.asarray(mesh.normals)
        same = np.allclose(normals[corners[:, 0]], normals[corners[:, 1]]) and np.allclose(
            normals[corners[:, 0]], normals[corners[:, 2]]
        )
        if not same:
            errors.append(f"{label}: flat normals differ across a face")
    if len(mesh.indices) and int(mesh.indices.max()) >= len(mesh.positions):
        errors.append(f"{label}: index out of range")
    return errors
