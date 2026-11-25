"""Preview renders show the mesh against the studio background."""

import io

import numpy as np
from PIL import Image

from chesscorpus.mesh import normalize_mesh
from chesscorpus.render import render_preview


def test_preview_frames_the_piece_against_the_background():
    count = 16
    angles = np.linspace(0, 2 * np.pi, count, endpoint=False)
    ring = np.stack(
        [0.3 * np.cos(angles), np.zeros(count), 0.3 * np.sin(angles)],
        axis=1,
    )
    apex = np.array([[0.0, 1.4, 0.0]])
    positions = np.vstack([ring, apex])
    faces = [(corner, (corner + 1) % count, count) for corner in range(count)]
    fixed, indices, _normals = normalize_mesh(positions, np.array(faces), shading="smooth")
    image = Image.open(io.BytesIO(render_preview(fixed, indices, size=96)))
    assert image.size == (96, 96)
    assert image.mode == "RGB"
    pixels = np.asarray(image)
    middle = float(pixels[:, 40:56].std())
    side = float(pixels[:, :12].std())
    assert middle > side + 5
