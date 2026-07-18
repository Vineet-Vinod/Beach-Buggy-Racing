from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DimensionRange:
    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]


@dataclass(frozen=True)
class AssetManifest:
    asset_id: str
    kind: str
    source: Path
    runtime: Path
    preview: Path
    metadata: Path
    dimensions: DimensionRange
    required_nodes: tuple[str, ...]
    required_materials: tuple[str, ...]
    required_animations: tuple[str, ...]

    @classmethod
    def load(cls, root: Path, path: Path) -> "AssetManifest":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path}: manifest root must be an object")
        if data.get("schema_version") != 1:
            raise ValueError(f"{path}: unsupported schema_version")

        try:
            asset_id = data["id"]
            kind = data["kind"]
            outputs = data["outputs"]
            dimensions = data["dimensions_m"]
            minimum = _dimension_vector(path, "minimum", dimensions["minimum"])
            maximum = _dimension_vector(path, "maximum", dimensions["maximum"])
            required_nodes = _name_list(path, "required_nodes", data["required_nodes"])
            required_materials = _name_list(path, "required_materials", data["required_materials"])
            required_animations = _name_list(path, "required_animations", data.get("required_animations", []))
        except (KeyError, TypeError) as error:
            raise ValueError(f"{path}: malformed manifest ({error})") from error

        if not isinstance(asset_id, str) or re.fullmatch(r"[a-z0-9_]+", asset_id) is None:
            raise ValueError(f"{path}: id must contain only lowercase letters, digits, and underscores")
        if not isinstance(kind, str) or not kind:
            raise ValueError(f"{path}: kind must be a non-empty string")
        for axis, lower, upper in zip("XYZ", minimum, maximum):
            if lower < 0.0 or upper <= 0.0 or lower > upper:
                raise ValueError(f"{path}: invalid {axis} dimension range [{lower}, {upper}]")

        return cls(
            asset_id=asset_id,
            kind=kind,
            source=_output_path(root, path, outputs, "blend", ".blend"),
            runtime=_output_path(root, path, outputs, "glb", ".glb"),
            preview=_output_path(root, path, outputs, "preview", ".png"),
            metadata=_output_path(root, path, outputs, "metadata", ".json"),
            dimensions=DimensionRange(minimum, maximum),
            required_nodes=required_nodes,
            required_materials=required_materials,
            required_animations=required_animations,
        )


def _dimension_vector(path: Path, label: str, values) -> tuple[float, float, float]:
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"{path}: dimensions_m.{label} must contain exactly three numbers")
    try:
        result = tuple(float(value) for value in values)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path}: dimensions_m.{label} contains a non-number") from error
    if not all(math.isfinite(value) for value in result):
        raise ValueError(f"{path}: dimensions_m.{label} values must be finite")
    return result


def _name_list(path: Path, label: str, values) -> tuple[str, ...]:
    if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{path}: {label} must be an array of non-empty strings")
    if len(values) != len(set(values)):
        raise ValueError(f"{path}: {label} contains duplicate names")
    return tuple(values)


def _output_path(root: Path, manifest_path: Path, outputs, key: str, suffix: str) -> Path:
    if not isinstance(outputs, dict) or not isinstance(outputs.get(key), str):
        raise ValueError(f"{manifest_path}: outputs.{key} must be a relative path")
    relative = Path(outputs[key])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{manifest_path}: outputs.{key} must stay within the repository")
    if relative.suffix.lower() != suffix:
        raise ValueError(f"{manifest_path}: outputs.{key} must end in {suffix}")
    return root / relative


def discover_manifests(root: Path) -> dict[str, AssetManifest]:
    manifests: dict[str, AssetManifest] = {}
    directory = root / "assets" / "manifests"
    for path in sorted(directory.glob("*.json")):
        manifest = AssetManifest.load(root, path)
        if manifest.asset_id in manifests:
            raise ValueError(f"duplicate asset id: {manifest.asset_id}")
        manifests[manifest.asset_id] = manifest
    return manifests
