from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import bpy
from mathutils import Vector

from .generators import GENERATORS
from .manifest import AssetManifest


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in tuple(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def configure_scene(asset_id: str):
    scene = bpy.context.scene
    scene.name = asset_id
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.018, 0.025, 0.036)

    runtime = bpy.data.collections.new("FB_RUNTIME")
    scene.collection.children.link(runtime)
    return runtime


def _runtime_objects():
    collection = bpy.data.collections.get("FB_RUNTIME")
    if collection is None:
        raise ValueError("scene has no FB_RUNTIME collection")
    return tuple(collection.all_objects)


def scene_bounds() -> tuple[Vector, Vector]:
    corners: list[Vector] = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in _runtime_objects():
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        corners.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
    if not corners:
        raise ValueError("runtime collection has no mesh geometry")
    return (
        Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners))),
        Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners))),
    )


def evaluated_triangle_count() -> int:
    total = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in _runtime_objects():
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            total += len(mesh.loop_triangles)
        finally:
            evaluated.to_mesh_clear()
    return total


def validate_scene(manifest: AssetManifest) -> dict:
    objects = {obj.name for obj in _runtime_objects()}
    materials = {material.name for material in bpy.data.materials}
    actions = {action.name for action in bpy.data.actions}
    errors: list[str] = []

    for name in manifest.required_nodes:
        if name not in objects:
            errors.append(f"missing required node: {name}")
    for name in manifest.required_materials:
        if name not in materials:
            errors.append(f"missing required material: {name}")
    for name in manifest.required_animations:
        if name not in actions:
            errors.append(f"missing required animation: {name}")

    bounds_min, bounds_max = scene_bounds()
    dimensions = bounds_max - bounds_min
    for axis, value, minimum, maximum in zip("XYZ", dimensions, manifest.dimensions.minimum, manifest.dimensions.maximum):
        if not minimum <= value <= maximum:
            errors.append(f"dimension {axis}={value:.3f}m outside [{minimum:.3f}, {maximum:.3f}]m")

    for obj in _runtime_objects():
        if obj.type == "MESH" and not obj.data.materials:
            errors.append(f"mesh has no material: {obj.name}")
        if any(abs(scale - 1.0) > 1e-4 for scale in obj.scale):
            errors.append(f"node has unapplied scale: {obj.name} {tuple(round(v, 4) for v in obj.scale)}")

    if errors:
        raise ValueError("asset validation failed:\n  - " + "\n  - ".join(errors))
    return {
        "bounds_min_m": [round(value, 6) for value in bounds_min],
        "bounds_max_m": [round(value, 6) for value in bounds_max],
        "dimensions_m": [round(value, 6) for value in dimensions],
        "mesh_count": sum(obj.type == "MESH" for obj in _runtime_objects()),
        "triangle_count": evaluated_triangle_count(),
    }


def _add_preview_stage() -> None:
    preview = bpy.data.collections.new("FB_PREVIEW")
    bpy.context.scene.collection.children.link(preview)

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0.0, 0.0, 0.0))
    ground = bpy.context.object
    ground.name = "preview_ground"
    for collection in tuple(ground.users_collection):
        collection.objects.unlink(ground)
    preview.objects.link(ground)
    material = bpy.data.materials.new("preview_ground_material")
    material.diffuse_color = (0.07, 0.11, 0.12, 1.0)
    ground.data.materials.append(material)

    camera_data = bpy.data.cameras.new("preview_camera")
    camera = bpy.data.objects.new("preview_camera", camera_data)
    preview.objects.link(camera)
    camera.location = (4.2, -5.1, 3.0)
    camera.rotation_euler = _look_at(camera.location, Vector((0.0, 0.0, 0.55)))
    camera_data.lens = 58
    bpy.context.scene.camera = camera

    key_data = bpy.data.lights.new("preview_key", "AREA")
    key_data.energy = 950
    key_data.shape = "DISK"
    key_data.size = 4.0
    key = bpy.data.objects.new("preview_key", key_data)
    preview.objects.link(key)
    key.location = (-3.5, -3.0, 6.0)
    key.rotation_euler = _look_at(key.location, Vector((0.0, 0.0, 0.5)))

    fill_data = bpy.data.lights.new("preview_fill", "AREA")
    fill_data.energy = 650
    fill_data.size = 3.0
    fill = bpy.data.objects.new("preview_fill", fill_data)
    preview.objects.link(fill)
    fill.location = (3.0, 1.5, 3.0)
    fill.rotation_euler = _look_at(fill.location, Vector((0.0, 0.0, 0.6)))


def _look_at(origin: Vector, target: Vector):
    return (target - origin).to_track_quat("-Z", "Y").to_euler()


def export_glb(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in _runtime_objects():
        obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )


def render_preview(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def _glb_json(path: Path) -> dict:
    contents = path.read_bytes()
    if len(contents) < 20 or contents[:4] != b"glTF":
        raise ValueError(f"{path}: not a binary glTF file")
    version, total_length = struct.unpack_from("<II", contents, 4)
    if version != 2 or total_length != len(contents):
        raise ValueError(f"{path}: invalid GLB header")
    json_length, chunk_type = struct.unpack_from("<II", contents, 12)
    if chunk_type != 0x4E4F534A:
        raise ValueError(f"{path}: first GLB chunk is not JSON")
    return json.loads(contents[20 : 20 + json_length].decode("utf-8"))


def validate_glb(manifest: AssetManifest) -> dict:
    data = _glb_json(manifest.runtime)
    nodes = {node.get("name") for node in data.get("nodes", [])}
    materials = {material.get("name") for material in data.get("materials", [])}
    animations = {animation.get("name") for animation in data.get("animations", [])}
    errors = []
    for name in manifest.required_nodes:
        if name not in nodes:
            errors.append(f"GLB missing node: {name}")
    for name in manifest.required_materials:
        if name not in materials:
            errors.append(f"GLB missing material: {name}")
    for name in manifest.required_animations:
        if name not in animations:
            errors.append(f"GLB missing named animation: {name}")
    if manifest.required_animations:
        skins = data.get("skins", [])
        if not skins:
            errors.append("animated GLB has no skin; raylib 6 cannot import node-only animation")
        elif not any(skin.get("joints") for skin in skins):
            errors.append("animated GLB skin has no joints")
    if not data.get("meshes"):
        errors.append("GLB contains no meshes")
    if not data.get("buffers") or "uri" in data["buffers"][0]:
        errors.append("GLB geometry buffer is not embedded")
    if errors:
        raise ValueError("GLB validation failed:\n  - " + "\n  - ".join(errors))
    return {
        "node_count": len(data.get("nodes", [])),
        "mesh_count": len(data.get("meshes", [])),
        "material_count": len(data.get("materials", [])),
        "animation_count": len(data.get("animations", [])),
        "skin_count": len(data.get("skins", [])),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while block := file.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _validate_generated_files(manifest: AssetManifest) -> dict:
    if not manifest.metadata.is_file():
        raise ValueError(f"missing asset metadata: {manifest.metadata}")
    if not manifest.preview.is_file():
        raise ValueError(f"missing asset preview: {manifest.preview}")
    if manifest.preview.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"asset preview is not a PNG file: {manifest.preview}")

    try:
        metadata = json.loads(manifest.metadata.read_text(encoding="utf-8"))
        expected_hashes = metadata["sha256"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"malformed asset metadata: {manifest.metadata}") from error
    if metadata.get("schema_version") != 1 or metadata.get("id") != manifest.asset_id:
        raise ValueError(f"asset metadata does not match manifest: {manifest.metadata}")

    actual_hashes = {
        "blend": _sha256(manifest.source),
        "glb": _sha256(manifest.runtime),
    }
    for key, actual in actual_hashes.items():
        if expected_hashes.get(key) != actual:
            raise ValueError(f"asset metadata has stale {key} hash: {manifest.metadata}")
    return {"sha256_verified": sorted(actual_hashes), "preview_png": True}


def build(manifest: AssetManifest, make_preview: bool = True) -> dict:
    generator = GENERATORS.get(manifest.asset_id)
    if generator is None:
        raise ValueError(f"no generator registered for {manifest.asset_id}")

    reset_scene()
    runtime = configure_scene(manifest.asset_id)
    generator(runtime)
    _add_preview_stage()
    scene_report = validate_scene(manifest)

    manifest.source.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(manifest.source), compress=True)
    export_glb(manifest.runtime)
    glb_report = validate_glb(manifest)
    if make_preview:
        render_preview(manifest.preview)

    report = {
        "schema_version": 1,
        "id": manifest.asset_id,
        "kind": manifest.kind,
        "coordinate_system": {
            "authoring": "right-handed, +Z up, +Y forward, meters",
            "glb": "right-handed, +Y up, +Z forward, meters",
        },
        "scene": scene_report,
        "glb": glb_report,
        "sha256": {
            "blend": _sha256(manifest.source),
            "glb": _sha256(manifest.runtime),
        },
    }
    manifest.metadata.parent.mkdir(parents=True, exist_ok=True)
    manifest.metadata.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def validate_saved(manifest: AssetManifest) -> dict:
    if not manifest.source.is_file():
        raise ValueError(f"missing Blender source: {manifest.source}")
    if not manifest.runtime.is_file():
        raise ValueError(f"missing runtime asset: {manifest.runtime}")
    bpy.ops.wm.open_mainfile(filepath=str(manifest.source))
    return {
        "scene": validate_scene(manifest),
        "glb": validate_glb(manifest),
        "artifacts": _validate_generated_files(manifest),
    }


def preview_saved(manifest: AssetManifest) -> None:
    if not manifest.source.is_file():
        raise ValueError(f"missing Blender source: {manifest.source}")
    bpy.ops.wm.open_mainfile(filepath=str(manifest.source))
    render_preview(manifest.preview)
