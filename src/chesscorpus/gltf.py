"""Minimal glTF 2.0 binary reader and writer for a single triangle mesh."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass

import numpy as np

GLB_MAGIC = 0x46546C67
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942

_COMPONENT_DTYPE = {
    5120: np.int8,
    5121: np.uint8,
    5122: np.int16,
    5123: np.uint16,
    5125: np.uint32,
    5126: np.float32,
}
_TYPE_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


@dataclass(frozen=True)
class Material:
    name: str
    base_color: tuple[float, float, float, float]
    metallic: float
    roughness: float


@dataclass
class MeshData:
    name: str
    positions: np.ndarray
    indices: np.ndarray
    normals: np.ndarray | None = None
    material: Material | None = None


def read_glb(data: bytes) -> MeshData:
    if len(data) < 20:
        raise ValueError("GLB is truncated")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC:
        raise ValueError(f"not a GLB file (magic {magic:#x})")
    if version != 2:
        raise ValueError(f"unsupported glTF version {version}")
    if length > len(data):
        raise ValueError("GLB length header exceeds the file size")

    offset = 12
    gltf = None
    blob = b""
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == JSON_CHUNK:
            gltf = json.loads(chunk.decode("utf-8").rstrip(" \x00"))
        elif chunk_type == BIN_CHUNK:
            blob = chunk
    if gltf is None:
        raise ValueError("GLB is missing a JSON chunk")
    return _mesh_from_gltf(gltf, blob)


def _read_accessor(gltf: dict, blob: bytes, index: int) -> np.ndarray:
    accessor = gltf["accessors"][index]
    if accessor.get("sparse"):
        raise ValueError("sparse accessors are not supported")
    view_index = accessor.get("bufferView")
    if view_index is None:
        raise ValueError("accessor is missing a buffer view")
    view = gltf["bufferViews"][view_index]
    dtype = np.dtype(_COMPONENT_DTYPE[accessor["componentType"]])
    components = _TYPE_COMPONENTS[accessor["type"]]
    count = int(accessor["count"])
    stride = int(view.get("byteStride", dtype.itemsize * components))
    start = int(view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    if stride == dtype.itemsize * components:
        array = np.frombuffer(blob, dtype=dtype, count=count * components, offset=start)
        return np.array(array).reshape(count, components)
    array = np.empty((count, components), dtype=dtype)
    for row in range(count):
        offset = start + row * stride
        array[row] = np.frombuffer(blob, dtype=dtype, count=components, offset=offset)
    return array


def _mesh_from_gltf(gltf: dict, blob: bytes) -> MeshData:
    meshes = gltf.get("meshes") or []
    if len(meshes) != 1:
        raise ValueError(f"expected 1 mesh, found {len(meshes)}")
    primitives = meshes[0].get("primitives") or []
    if len(primitives) != 1:
        raise ValueError(f"expected 1 primitive, found {len(primitives)}")
    primitive = primitives[0]
    if int(primitive.get("mode", 4)) != 4:
        raise ValueError(f"expected triangles, found mode {primitive.get('mode')}")
    attributes = primitive.get("attributes") or {}
    if "POSITION" not in attributes:
        raise ValueError("mesh has no POSITION attribute")
    positions = _read_accessor(gltf, blob, attributes["POSITION"]).astype(np.float32)
    if positions.shape[1] != 3:
        raise ValueError("POSITION is not VEC3")
    if "indices" not in primitive:
        raise ValueError("mesh has no indices")
    indices = _read_accessor(gltf, blob, primitive["indices"]).reshape(-1, 3).astype(np.int64)
    normals = None
    if "NORMAL" in attributes:
        normals = _read_accessor(gltf, blob, attributes["NORMAL"]).astype(np.float32)
    material = None
    if "material" in primitive:
        source = (gltf.get("materials") or [])[primitive["material"]]
        pbr = source.get("pbrMetallicRoughness") or {}
        color = pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])
        material = Material(
            name=str(source.get("name") or "material"),
            base_color=(float(color[0]), float(color[1]), float(color[2]), float(color[3])),
            metallic=float(pbr.get("metallicFactor", 1.0)),
            roughness=float(pbr.get("roughnessFactor", 1.0)),
        )
    name = str(meshes[0].get("name") or (gltf.get("nodes") or [{}])[0].get("name") or "mesh")
    return MeshData(name, positions, indices, normals, material)


def write_glb(mesh: MeshData) -> bytes:
    if mesh.normals is None:
        raise ValueError("normals are required")
    positions = np.ascontiguousarray(mesh.positions, dtype=np.float32)
    normals = np.ascontiguousarray(mesh.normals, dtype=np.float32)
    indices = np.ascontiguousarray(mesh.indices, dtype=np.int64)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("positions must have shape (N, 3)")
    if normals.shape != positions.shape:
        raise ValueError("normals must match positions")
    if indices.ndim != 2 or indices.shape[1] != 3:
        raise ValueError("indices must have shape (F, 3)")
    if len(indices) and int(indices.max()) >= len(positions):
        raise ValueError("index out of range")

    index_max = int(indices.max()) if len(indices) else 0
    if index_max > 65535:
        index_array = np.ascontiguousarray(indices, dtype=np.uint32)
        index_component = 5125
    else:
        index_array = np.ascontiguousarray(indices, dtype=np.uint16)
        index_component = 5123

    position_bytes = positions.tobytes()
    normal_bytes = normals.tobytes()
    index_bytes = index_array.tobytes()
    padding = (4 - (len(index_bytes) % 4)) % 4
    blob = position_bytes + normal_bytes + index_bytes + (b"\x00" * padding)

    position_min = [float(value) for value in positions.min(axis=0)]
    position_max = [float(value) for value in positions.max(axis=0)]
    primitive: dict = {
        "attributes": {"POSITION": 0, "NORMAL": 1},
        "indices": 2,
        "mode": 4,
    }
    gltf: dict = {
        "asset": {"version": "2.0", "generator": "chesscorpus"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": mesh.name, "mesh": 0}],
        "meshes": [{"name": mesh.name, "primitives": [primitive]}],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": int(len(positions)),
                "type": "VEC3",
                "min": position_min,
                "max": position_max,
            },
            {
                "bufferView": 1,
                "componentType": 5126,
                "count": int(len(normals)),
                "type": "VEC3",
            },
            {
                "bufferView": 2,
                "componentType": index_component,
                "count": int(indices.size),
                "type": "SCALAR",
            },
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(position_bytes),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": len(position_bytes),
                "byteLength": len(normal_bytes),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": len(position_bytes) + len(normal_bytes),
                "byteLength": len(index_bytes),
                "target": 34963,
            },
        ],
        "buffers": [{"byteLength": len(blob)}],
    }
    if mesh.material is not None:
        primitive["material"] = 0
        color = [round(float(channel), 6) for channel in mesh.material.base_color]
        gltf["materials"] = [
            {
                "name": mesh.material.name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": color,
                    "metallicFactor": round(float(mesh.material.metallic), 6),
                    "roughnessFactor": round(float(mesh.material.roughness), 6),
                },
            }
        ]

    payload = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    payload += b" " * ((4 - (len(payload) % 4)) % 4)
    total = 12 + 8 + len(payload) + 8 + len(blob)
    header = struct.pack("<III", GLB_MAGIC, 2, total)
    json_header = struct.pack("<II", len(payload), JSON_CHUNK)
    bin_header = struct.pack("<II", len(blob), BIN_CHUNK)
    return header + json_header + payload + bin_header + blob
