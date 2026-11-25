"""Embedded PBR colors for the two sides."""

from __future__ import annotations

import numpy as np

from chesscorpus.gltf import Material


def srgb_u8_to_linear(channel: int) -> float:
    value = channel / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _linear_rgb(srgb: tuple[int, int, int]) -> tuple[float, float, float, float]:
    red, green, blue = (round(srgb_u8_to_linear(channel), 6) for channel in srgb)
    return (red, green, blue, 1.0)


# Ivory and ebony, stored as linear baseColorFactor values.
WHITE = Material("white", _linear_rgb((244, 236, 220)), metallic=0.0, roughness=0.58)
BLACK = Material("black", _linear_rgb((38, 38, 42)), metallic=0.0, roughness=0.46)
MATERIALS = {"white": WHITE, "black": BLACK}


def luminance(color: tuple[float, float, float, float]) -> float:
    red, green, blue, _alpha = color
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def preview_base_color() -> np.ndarray:
    return np.array(WHITE.base_color[:3], dtype=np.float64)
