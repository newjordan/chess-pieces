"""Software preview renders of a mesh. No GPU required."""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

from chesscorpus.materials import preview_base_color

_BACKGROUND_TOP = np.array([0.80, 0.78, 0.75], dtype=np.float64)
_BACKGROUND_BOTTOM = np.array([0.56, 0.55, 0.53], dtype=np.float64)


def _unit(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def _camera(
    positions: np.ndarray, fov: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    points = np.asarray(positions, dtype=np.float64)
    height = float(points[:, 1].max())
    center = np.array([0.0, height * 0.46, 0.0])
    radius = float(np.linalg.norm(points - center, axis=1).max())
    distance = radius / np.sin(fov / 2.0) * 1.08
    eye = center + _unit(np.array([0.78, 0.52, 1.18])) * distance
    backward = _unit(eye - center)
    right = _unit(np.cross(np.array([0.0, 1.0, 0.0]), backward))
    up = np.cross(backward, right)
    return eye, right, up, backward


def _shade_faces(
    positions: np.ndarray, indices: np.ndarray, toward_camera: np.ndarray
) -> np.ndarray:
    points = np.asarray(positions, dtype=np.float64)
    triangles = np.asarray(indices, dtype=np.int64)
    normal = np.cross(
        points[triangles[:, 1]] - points[triangles[:, 0]],
        points[triangles[:, 2]] - points[triangles[:, 0]],
    )
    length = np.linalg.norm(normal, axis=1, keepdims=True)
    normal = np.divide(normal, np.maximum(length, 1e-12))
    key = _unit(np.array([0.32, 0.88, 0.42]))
    fill = _unit(np.array([-0.65, 0.28, -0.22]))
    rim = _unit(np.array([-0.15, 0.15, -0.95]))
    key_term = np.clip(normal @ key, 0.0, 1.0)
    fill_term = np.clip(normal @ fill, 0.0, 1.0)
    rim_term = np.clip(normal @ rim, 0.0, 1.0)
    half = _unit(key + toward_camera)
    specular = np.clip(normal @ half, 0.0, 1.0) ** 48 * 0.16
    base = preview_base_color()
    color = base * (0.20 + 0.74 * key_term + 0.20 * fill_term + 0.06 * rim_term)[:, None]
    color += specular[:, None]
    facing = normal @ toward_camera
    color[facing <= 0.0] = 0.0
    color[length[:, 0] < 1e-12] = 0.0
    return np.clip(color, 0.0, 1.0)


def _background(size: int) -> np.ndarray:
    gradient = np.linspace(0.0, 1.0, size, dtype=np.float64)[:, None]
    column = _BACKGROUND_TOP * (1.0 - gradient) + _BACKGROUND_BOTTOM * gradient
    return np.broadcast_to(column, (size, size, 3)).copy()


def _paint_shadow(
    image: np.ndarray,
    depth: np.ndarray,
    positions: np.ndarray,
    eye: np.ndarray,
    right: np.ndarray,
    up: np.ndarray,
    backward: np.ndarray,
    fov: float,
) -> None:
    points = np.asarray(positions, dtype=np.float64)
    foot = points[points[:, 1] <= max(float(points[:, 1].max()) * 0.05, 1e-4)]
    if len(foot) < 3:
        foot = points
    radius_x = max(float(np.max(np.abs(foot[:, 0]))) * 1.08, 1e-3)
    radius_z = max(float(np.max(np.abs(foot[:, 2]))) * 1.08, 1e-3)
    size = image.shape[0]
    pixels = (np.arange(size) + 0.5) / size * 2.0 - 1.0
    screen_x, screen_y = np.meshgrid(pixels, pixels[::-1])
    scale = np.tan(fov / 2.0)
    directions = (
        right * (screen_x * scale)[..., None] + up * (screen_y * scale)[..., None] - backward
    )
    denom = directions[..., 1]
    valid = np.abs(denom) > 1e-8
    distance = np.zeros(denom.shape, dtype=np.float64)
    distance[valid] = -eye[1] / denom[valid]
    hit = eye + distance[..., None] * directions
    ellipse = (hit[..., 0] / radius_x) ** 2 + (hit[..., 2] / radius_z) ** 2
    mask = valid & (distance > 0.0) & (ellipse < 1.0)
    strength = (np.clip(1.0 - ellipse, 0.0, 1.0) ** 1.35) * 0.42
    image[mask] *= (1.0 - strength[mask])[..., None]
    forward = -backward
    depth[mask] = distance[mask] * np.sum(directions[mask] * forward, axis=-1)


def _rasterize(image, depth, px, py, pz, colors, indices) -> None:
    height, width = image.shape[:2]
    for face, color in enumerate(colors):
        if color[0] == 0.0 and color[1] == 0.0 and color[2] == 0.0:
            continue
        corners = indices[face]
        x = px[corners]
        y = py[corners]
        z = pz[corners]
        if np.any(z <= 1e-4):
            continue
        min_x = max(int(np.floor(np.min(x))), 0)
        max_x = min(int(np.ceil(np.max(x))), width - 1)
        min_y = max(int(np.floor(np.min(y))), 0)
        max_y = min(int(np.ceil(np.max(y))), height - 1)
        if min_x > max_x or min_y > max_y:
            continue
        x0, x1, x2 = float(x[0]), float(x[1]), float(x[2])
        y0, y1, y2 = float(y[0]), float(y[1]), float(y[2])
        z0, z1, z2 = float(z[0]), float(z[1]), float(z[2])
        denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denominator) < 1e-8:
            continue
        xs = np.arange(min_x, max_x + 1) + 0.5
        ys = np.arange(min_y, max_y + 1) + 0.5
        grid_x, grid_y = np.meshgrid(xs, ys)
        weight_0 = ((y1 - y2) * (grid_x - x2) + (x2 - x1) * (grid_y - y2)) / denominator
        weight_1 = ((y2 - y0) * (grid_x - x2) + (x0 - x2) * (grid_y - y2)) / denominator
        weight_2 = 1.0 - weight_0 - weight_1
        covered = (weight_0 >= 0.0) & (weight_1 >= 0.0) & (weight_2 >= 0.0)
        if not np.any(covered):
            continue
        inverse = weight_0 / z0 + weight_1 / z1 + weight_2 / z2
        view_z = np.full(inverse.shape, np.inf, dtype=np.float64)
        usable = covered & (inverse > 1e-8)
        view_z[usable] = 1.0 / inverse[usable]
        stored = depth[min_y : max_y + 1, min_x : max_x + 1]
        update = usable & (view_z < stored)
        if not np.any(update):
            continue
        stored[update] = view_z[update]
        image[min_y : max_y + 1, min_x : max_x + 1][update] = color


def render_preview(positions: np.ndarray, indices: np.ndarray, *, size: int = 768) -> bytes:
    """Return a square RGB PNG of the mesh from a consistent three-quarter camera."""
    points = np.asarray(positions, dtype=np.float64)
    triangles = np.asarray(indices, dtype=np.int64)
    fov = np.deg2rad(32.0)
    eye, right, up, backward = _camera(points, fov)
    view = _unit(-backward)
    colors = _shade_faces(points, triangles, _unit(backward))
    relative = points - eye
    forward_depth = relative @ view
    scale = np.tan(fov / 2.0)
    pixel_x = ((relative @ right) / forward_depth / scale * 0.5 + 0.5) * size
    pixel_y = (1.0 - ((relative @ up) / forward_depth / scale * 0.5 + 0.5)) * size

    image = _background(size)
    depth = np.full((size, size), np.inf, dtype=np.float64)
    _paint_shadow(image, depth, points, eye, right, up, backward, fov)
    _rasterize(image, depth, pixel_x, pixel_y, forward_depth, colors, triangles)

    encoded = np.clip(image, 0.0, 1.0) ** (1.0 / 2.2)
    picture = Image.fromarray(np.round(encoded * 255.0).astype(np.uint8), mode="RGB")
    buffer = io.BytesIO()
    picture.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
