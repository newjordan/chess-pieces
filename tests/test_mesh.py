"""Orientation math and the game-ready normalize step."""

import numpy as np

from chesscorpus.mesh import basis_from_up, mesh_metrics, normalize_mesh, outward_fraction


def _cone_along_x(*, flip: bool) -> tuple[np.ndarray, np.ndarray]:
    count = 24
    angles = np.linspace(0, 2 * np.pi, count, endpoint=False)
    ring = np.stack(
        [np.full(count, -1.0), 0.45 * np.cos(angles), 0.45 * np.sin(angles)],
        axis=1,
    )
    apex = np.array([[1.0, 0.0, 0.0]])
    positions = np.vstack([ring, apex])
    faces = []
    apex_index = count
    for corner in range(count):
        nxt = (corner + 1) % count
        faces.append((corner, nxt, apex_index))
    indices = np.array(faces, dtype=np.int64)
    if flip:
        indices[:, [1, 2]] = indices[:, [2, 1]]
    return positions, indices


def test_basis_is_a_rotation_onto_y():
    axes = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    for axis in axes:
        transform = basis_from_up(np.array(axis, dtype=np.float64))
        assert np.isclose(np.linalg.det(transform), 1.0)
        mapped = transform @ np.array(axis, dtype=np.float64)
        assert np.allclose(mapped, [0.0, 1.0, 0.0], atol=1e-8)


def test_sideways_inverted_cone_stands_up():
    positions, indices = _cone_along_x(flip=True)
    assert outward_fraction(positions, indices) < 0.5
    original_height = float(np.ptp(positions[:, 0]))
    fixed, faces, normals = normalize_mesh(positions, indices, shading="smooth")
    metrics = mesh_metrics(fixed, faces)
    assert abs(float(metrics["min"][1])) <= 1e-4
    assert abs(float(metrics["center"][0])) <= 1e-4
    assert abs(float(metrics["center"][2])) <= 1e-4
    assert metrics["span"][1] == max(metrics["span"])
    assert np.isclose(metrics["span"][1], original_height, atol=1e-4)
    assert metrics["outward"] > 0.5
    assert np.allclose(np.linalg.norm(normals, axis=1), 1.0, atol=1e-5)


def test_normalize_is_idempotent_for_both_shading_modes():
    positions, indices = _cone_along_x(flip=True)
    for shading in ("smooth", "flat"):
        once = normalize_mesh(positions, indices, shading=shading)
        twice = normalize_mesh(once[0], once[1], shading=shading)
        for left, right in zip(once, twice, strict=True):
            assert np.allclose(left, right, atol=1e-5)


def test_existing_upright_mesh_keeps_its_axis():
    count = 20
    angles = np.linspace(0, 2 * np.pi, count, endpoint=False)
    low = np.stack([0.3 * np.cos(angles), np.zeros(count), 0.3 * np.sin(angles)], axis=1)
    high = np.stack([0.2 * np.cos(angles), np.full(count, 2.0), 0.2 * np.sin(angles)], axis=1)
    positions = np.vstack([low, high])
    faces = []
    for corner in range(count):
        nxt = (corner + 1) % count
        faces.append((corner, nxt, count + nxt))
        faces.append((corner, count + nxt, count + corner))
    indices = np.array(faces, dtype=np.int64)
    fixed, _faces, _normals = normalize_mesh(positions, indices, shading="smooth")
    metrics = mesh_metrics(fixed, _faces)
    assert np.isclose(metrics["span"][1], 2.0, atol=1e-4)
    assert metrics["span"][1] > metrics["span"][0]
    assert metrics["span"][1] > metrics["span"][2]


def test_asymmetric_crown_turns_to_face_negative_z():
    base_count = 36
    crown_count = 12
    base_angles = np.linspace(0, 2 * np.pi, base_count, endpoint=False)
    crown_angles = np.linspace(0, 2 * np.pi, crown_count, endpoint=False)
    base = np.stack(
        [np.full(base_count, -1.0), 0.35 * np.cos(base_angles), 0.35 * np.sin(base_angles)],
        axis=1,
    )
    crown = np.stack(
        [np.full(crown_count, 1.0), 0.12 * np.cos(crown_angles), 0.12 * np.sin(crown_angles)],
        axis=1,
    )
    nose = np.array([[1.05, 0.0, 0.9], [0.9, 0.08, 0.55], [0.9, -0.08, 0.55]])
    positions = np.vstack([base, crown, nose])
    faces = []
    for corner in range(base_count):
        nxt = (corner + 1) % base_count
        crown_index = base_count + int(corner * crown_count / base_count)
        faces.append((corner, nxt, crown_index))
    nose_start = base_count + crown_count
    faces.append((base_count, base_count + 1, nose_start))
    faces.append((base_count + 1, base_count + 2, nose_start + 1))
    faces.append((base_count + 2, base_count, nose_start + 2))
    indices = np.array(faces, dtype=np.int64)
    fixed, _faces, _normals = normalize_mesh(positions, indices, shading="smooth")
    crown_fixed = fixed[fixed[:, 1] >= fixed[:, 1].max() * 0.7]
    offset = crown_fixed[:, [0, 2]].mean(axis=0)
    assert offset[1] < -0.05
    assert abs(offset[1]) > abs(offset[0])
