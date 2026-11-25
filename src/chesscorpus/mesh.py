"""Mesh measurements and the game-ready orientation fix."""

from __future__ import annotations

import numpy as np

_AXIS_NAME = {0: "X", 1: "Y", 2: "Z"}


def outward_fraction(positions: np.ndarray, indices: np.ndarray) -> float:
    """Share of triangles whose winding faces away from the vertex centroid."""
    if len(indices) == 0:
        return 1.0
    points = np.asarray(positions, dtype=np.float64)
    triangles = np.asarray(indices, dtype=np.int64)
    first = points[triangles[:, 0]]
    second = points[triangles[:, 1]]
    third = points[triangles[:, 2]]
    normal = np.cross(second - first, third - first)
    length = np.linalg.norm(normal, axis=1)
    valid = length > 1e-12
    if not np.any(valid):
        return 1.0
    direction = normal[valid] / length[valid, None]
    centers = (first + second + third)[valid] / 3.0
    dots = np.sum(direction * (centers - points.mean(axis=0)), axis=1)
    return float(np.mean(dots > 0))


def mesh_metrics(positions: np.ndarray, indices: np.ndarray) -> dict:
    points = np.asarray(positions, dtype=np.float64)
    triangles = np.asarray(indices)
    lows = points.min(axis=0)
    highs = points.max(axis=0)
    unique = np.unique(np.round(points, 5), axis=0).shape[0]
    return {
        "vertices": int(points.shape[0]),
        "faces": int(len(triangles)),
        "uniquePositions": int(unique),
        "min": lows,
        "max": highs,
        "span": highs - lows,
        "center": (lows + highs) / 2.0,
        "outward": outward_fraction(points, triangles),
    }


def published_stats(positions: np.ndarray, indices: np.ndarray) -> dict:
    metrics = mesh_metrics(positions, indices)
    return {
        "vertices": metrics["vertices"],
        "faces": metrics["faces"],
        "uniquePositions": metrics["uniquePositions"],
        "height": round(float(metrics["span"][1]), 4),
        "width": round(float(metrics["span"][0]), 4),
        "depth": round(float(metrics["span"][2]), 4),
    }


def detect_up_axis(positions: np.ndarray) -> np.ndarray:
    """Return the unit vector that points from the base toward the crown.

    The long axis is the height. Its heavier end is the base, because a chess
    piece rests on a wide foot and tapers toward the crown.
    """
    points = np.asarray(positions, dtype=np.float64)
    best_score: tuple[float, int] | None = None
    best = np.array([0.0, 1.0, 0.0])
    for axis in range(3):
        column = points[:, axis]
        span = float(column.max() - column.min())
        if span <= 1e-8:
            continue
        tolerance = span * 0.02
        near_min = int(np.sum(column <= column.min() + tolerance))
        near_max = int(np.sum(column >= column.max() - tolerance))
        direction = 1.0 if near_min >= near_max else -1.0
        support = near_min if direction > 0 else near_max
        score = (span, support)
        if best_score is None or score > best_score:
            best_score = score
            best = np.zeros(3, dtype=np.float64)
            best[axis] = direction
    if best_score is None:
        raise ValueError("mesh has no extent")
    return best


def basis_from_up(up: np.ndarray) -> np.ndarray:
    """Rows of a right-handed rotation that maps `up` onto +Y and prefers +Z forward."""
    y_axis = np.asarray(up, dtype=np.float64)
    y_axis = y_axis / np.linalg.norm(y_axis)
    hint = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(y_axis, hint))) > 0.99:
        hint = np.array([1.0, 0.0, 0.0])
    x_axis = np.cross(y_axis, hint)
    x_axis /= np.linalg.norm(x_axis)
    z_axis = np.cross(x_axis, y_axis)
    return np.stack([x_axis, y_axis, z_axis], axis=0)


def _recenter(positions: np.ndarray) -> np.ndarray:
    placed = np.array(positions, dtype=np.float32, copy=True)
    placed[:, 1] -= placed[:, 1].min()
    placed[:, 0] -= (placed[:, 0].min() + placed[:, 0].max()) * np.float32(0.5)
    placed[:, 2] -= (placed[:, 2].min() + placed[:, 2].max()) * np.float32(0.5)
    placed[:, 1] -= placed[:, 1].min()
    return placed


def _align_facing(positions: np.ndarray) -> np.ndarray:
    """Yaw asymmetric crowns so they point down -Z. Symmetric pieces stay put."""
    points = np.array(positions, dtype=np.float64, copy=True)
    height = float(points[:, 1].max() - points[:, 1].min())
    if height <= 1e-8:
        return positions
    crown = points[points[:, 1] >= points[:, 1].min() + 0.55 * height]
    if len(crown) < 8:
        return positions
    offset = crown[:, [0, 2]].mean(axis=0)
    radial = float(np.linalg.norm(points[:, [0, 2]], axis=1).max())
    magnitude = float(np.linalg.norm(offset))
    if radial <= 1e-8 or magnitude < 0.12 * radial:
        return positions
    phi = float(np.arctan2(offset[0], -offset[1]))
    if abs(phi) < np.deg2rad(8.0):
        return positions
    cosine, sine = float(np.cos(phi)), float(np.sin(phi))
    x_coord = points[:, 0].copy()
    z_coord = points[:, 2].copy()
    points[:, 0] = x_coord * cosine + z_coord * sine
    points[:, 2] = -x_coord * sine + z_coord * cosine
    return points


def _unit_normals(normals: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    safe = np.array(normals, dtype=np.float64, copy=True)
    usable = lengths[:, 0] >= 1e-12
    safe[usable] /= lengths[usable]
    safe[~usable] = np.array([0.0, 1.0, 0.0])
    return safe.astype(np.float32)


def vertex_normals(positions: np.ndarray, indices: np.ndarray) -> np.ndarray:
    points = np.asarray(positions, dtype=np.float64)
    triangles = np.asarray(indices, dtype=np.int64)
    first = points[triangles[:, 0]]
    second = points[triangles[:, 1]]
    third = points[triangles[:, 2]]
    face = np.cross(second - first, third - first)
    normals = np.zeros_like(points)
    np.add.at(normals, triangles[:, 0], face)
    np.add.at(normals, triangles[:, 1], face)
    np.add.at(normals, triangles[:, 2], face)
    return _unit_normals(normals)


def flat_shaded(
    positions: np.ndarray, indices: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One vertex per corner so every edge is a hard edge."""
    points = np.asarray(positions, dtype=np.float64)
    triangles = np.asarray(indices, dtype=np.int64)
    first = points[triangles[:, 0]]
    second = points[triangles[:, 1]]
    third = points[triangles[:, 2]]
    face = np.cross(second - first, third - first)
    lengths = np.linalg.norm(face, axis=1, keepdims=True)
    normal = np.divide(face, np.maximum(lengths, 1e-12))
    normal[lengths[:, 0] < 1e-12] = np.array([0.0, 1.0, 0.0])
    flat_positions = np.stack([first, second, third], axis=1).reshape(-1, 3)
    flat_normals = np.repeat(normal, 3, axis=0)
    flat_indices = np.arange(len(triangles) * 3, dtype=np.int64).reshape(-1, 3)
    return flat_positions.astype(np.float32), flat_indices, flat_normals.astype(np.float32)


def _unflatten_export(positions: np.ndarray, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Weld a previous flat export back together so normalize can run again.

    Flat files from this package store one vertex per corner and sequential
    indices. Welding those exact copies restores the shared-vertex mesh.
    Other files are returned unchanged, so a first import keeps its topology.
    """
    points = np.asarray(positions)
    triangles = np.asarray(indices, dtype=np.int64)
    if points.shape[0] % 3 != 0:
        return np.asarray(positions, dtype=np.float64), triangles
    sequential = np.arange(points.shape[0], dtype=np.int64).reshape(-1, 3)
    if points.shape[0] != triangles.shape[0] * 3 or not np.array_equal(triangles, sequential):
        return np.asarray(positions, dtype=np.float64), triangles
    keys = np.round(np.ascontiguousarray(points, dtype=np.float32).astype(np.float64), 6)
    _unique, first, inverse = np.unique(keys, axis=0, return_index=True, return_inverse=True)
    welded = np.asarray(points, dtype=np.float64)[first]
    return welded, inverse[triangles]


def normalize_mesh(
    positions: np.ndarray,
    indices: np.ndarray,
    *,
    shading: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Make a piece upright, base-grounded, centered, and front-facing.

    +Y is up, the base sits on y=0, the footprint is centered on x and z, and
    an asymmetric crown yaws to face -Z. Winding is flipped when the surface
    faces inward. `flat` shading unwinds shared vertices; `smooth` keeps them.
    """
    if shading not in ("flat", "smooth"):
        raise ValueError(f"unknown shading {shading!r}")
    points, triangles = _unflatten_export(positions, indices)
    triangles = np.array(triangles, dtype=np.int64, copy=True)
    if outward_fraction(points, triangles) < 0.5:
        triangles[:, [1, 2]] = triangles[:, [2, 1]]
    transform = basis_from_up(detect_up_axis(points))
    points = points @ transform.T
    points = _recenter(points).astype(np.float64)
    # Recenter after each yaw. One pass can leave the crown past the
    # trigger, so repeat until a second run would leave the mesh alone.
    for _ in range(4):
        turned = _align_facing(points)
        if np.allclose(turned, points, atol=1e-6):
            break
        points = _recenter(turned).astype(np.float64)
    if shading == "flat":
        points, triangles, normals = flat_shaded(points, triangles)
        points = _recenter(points)
    else:
        points = _recenter(points)
        normals = vertex_normals(points, triangles)
    metrics = mesh_metrics(points, triangles)
    span = metrics["span"]
    upright = float(span[1]) + 1e-4 >= max(float(span[0]), float(span[2]))
    grounded = abs(float(metrics["min"][1])) <= 1e-4
    if not upright or not grounded or metrics["outward"] < 0.5:
        axis = _AXIS_NAME[int(np.argmax(np.abs(detect_up_axis(positions))))]
        raise RuntimeError(
            f"normalize left a mesh unusable (up candidate {axis}, span {span.tolist()})"
        )
    return points, triangles, normals
