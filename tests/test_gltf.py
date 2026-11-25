"""GLB bytes round-trip through the reader."""

import numpy as np

from chesscorpus.gltf import MeshData, read_glb, write_glb
from chesscorpus.materials import BLACK, WHITE
from chesscorpus.mesh import normalize_mesh


def test_roundtrip_keeps_geometry_and_material():
    count = 12
    angles = np.linspace(0, 2 * np.pi, count, endpoint=False)
    ring = np.stack([np.full(count, -1.0), 0.2 * np.cos(angles), 0.2 * np.sin(angles)], axis=1)
    positions = np.vstack([ring, [[1.2, 0.0, 0.0]]])
    indices = np.array([(i, (i + 1) % count, count) for i in range(count)], dtype=np.int64)
    fixed, faces, normals = normalize_mesh(positions, indices, shading="smooth")
    mesh = MeshData("king", fixed, faces, normals, WHITE)
    restored = read_glb(write_glb(mesh))
    assert restored.name == "king"
    assert np.allclose(restored.positions, fixed)
    assert np.array_equal(restored.indices, faces)
    assert restored.normals is not None
    assert np.allclose(restored.normals, normals, atol=1e-6)
    assert restored.material is not None
    assert restored.material.name == "white"
    assert restored.material.base_color[0] > BLACK.base_color[0]


def test_large_index_uses_unsigned_int():
    count = 70000
    positions = np.zeros((count, 3), dtype=np.float32)
    positions[:, 1] = np.linspace(0, 1, count)
    indices = np.arange(count - (count % 3), dtype=np.int64).reshape(-1, 3)
    normals = np.zeros_like(positions)
    normals[:, 1] = 1
    payload = write_glb(MeshData("pawn", positions, indices, normals, BLACK))
    restored = read_glb(payload)
    assert restored.indices.max() == indices.max()
    assert restored.material is not None
    assert restored.material.name == "black"
