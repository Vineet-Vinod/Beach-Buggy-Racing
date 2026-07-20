"""Generate the single anonymous Standard Driver used by every car."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from asset_helpers import (ASSET_PROP, asset_objects, bar, build_rigid_rig,
                           create_rig_action, cube, cylinder, empty,
                           export_asset, material, reset_scene, sphere, torus)


DRIVERS = {
    "standard_driver": {
        "display_name": "Standard Driver",
        "silhouette": "anonymous helmeted formula racing driver",
        "shirt": (0.018, 0.035, 0.075, 1),
        "accent": (0.96, 0.22, 0.025, 1),
    },
}

REQUIRED = ["driver_root", "root", "head", "arm_L", "arm_R",
            "driver_rig", "driver_root_bone", "head_bone", "arm_L_bone",
            "arm_R_bone"]


def make_standard_driver(torso, head, arm_l, arm_r, leg_l, leg_r, mats):
    """Build the anonymous, fully equipped driver shared by every car."""
    sphere("torso_shell", (0, 0.01, 0.08), (0.245, 0.145, 0.285),
           mats["shirt"], torso, 20, 12)
    sphere("waist", (0, 0.015, -0.125), (0.195, 0.125, 0.155),
           mats["shirt"], torso, 18, 10)
    cube("chest_panel", (0, -0.139, 0.115), (0.25, 0.018, 0.30),
         mats["detail"], torso, 0.018)
    cube("harness_buckle", (0, -0.155, 0.025), (0.080, 0.025, 0.085),
         mats["metal"], torso, 0.014)
    for side in (-1, 1):
        bar(f"suit_piping_{side:+}", (side * 0.120, -0.148, 0.26),
            (side * 0.078, -0.151, -0.05), 0.010,
            mats["accent"], torso)
        bar(f"harness_{side:+}", (side * 0.105, -0.151, 0.25),
            (side * 0.035, -0.168, 0.045), 0.018,
            mats["dark"], torso)
    cylinder("balaclava_neck", (0, 0, 0.365), 0.064, 0.105,
             mats["dark"], torso, vertices=16, bevel=0.010)
    torus("hans_collar", (0, 0, 0.325), 0.082, 0.022,
          mats["dark"], torso, major_segments=18, minor_segments=6)

    # Full-face helmet: smooth shell, chin bar, smoked visor and simple
    # center stripe. There is deliberately no face or individual identity.
    sphere("helmet_shell", (0, 0.0, 0.105), (0.145, 0.128, 0.175),
           mats["detail"], head, 22, 14)
    sphere("helmet_chin_guard", (0, -0.030, 0.012),
           (0.118, 0.108, 0.098), mats["detail"], head, 18, 10)
    cube("helmet_visor", (0, -0.127, 0.112),
         (0.225, 0.018, 0.075), mats["glass"], head, 0.018)
    cube("helmet_visor_brow", (0, -0.125, 0.160),
         (0.238, 0.023, 0.025), mats["dark"], head, 0.010)
    cube("helmet_center_stripe", (0, 0.000, 0.272),
         (0.045, 0.190, 0.018), mats["accent"], head, 0.007)
    for side in (-1, 1):
        cylinder(f"helmet_hinge_{side:+}", (side * 0.142, -0.025, 0.105),
                 0.028, 0.018, mats["accent"], head,
                 rotation=(0, math.pi / 2, 0), vertices=12, bevel=0.004)
        cube(f"helmet_side_panel_{side:+}",
             (side * 0.130, 0.025, 0.010),
             (0.025, 0.105, 0.080), mats["shirt"], head, 0.009)
    for x in (-0.045, 0.0, 0.045):
        cube(f"helmet_vent_{x:+}", (x, -0.148, -0.005),
             (0.022, 0.010, 0.010), mats["dark"], head, 0.003)

    # Long sleeves and gloves keep all skin covered. Hands converge on the
    # common steering-wheel hard point used by every Formula livery.
    for side, arm in ((-1, arm_l), (1, arm_r)):
        sphere(f"shoulder_{side:+}", (0, 0, 0.070),
               (0.055, 0.060, 0.068), mats["shirt"], arm, 16, 10)
        elbow = (side * 0.045, -0.195, -0.020)
        hand = (-side * 0.145, -0.410, -0.080)
        bar(f"upper_arm_{side:+}", (0, 0, 0.055), elbow,
            0.047, mats["shirt"], arm)
        bar(f"forearm_{side:+}", elbow, hand, 0.044,
            mats["shirt"], arm)
        sphere(f"glove_{side:+}", hand, (0.048, 0.040, 0.054),
               mats["gloves"], arm, 16, 10)
        torus(f"glove_cuff_{side:+}",
              tuple(elbow[index] * 0.22 + hand[index] * 0.78
                    for index in range(3)),
              0.047, 0.009, mats["accent"], arm,
              rotation=(math.radians(68), 0, 0),
              major_segments=16, minor_segments=6)

    for side, leg in ((-1, leg_l), (1, leg_r)):
        knee = (0, -0.305, -0.105)
        ankle = (0, -0.500, -0.315)
        bar(f"thigh_{side:+}", (0, 0, 0.075), knee,
            0.082, mats["shirt"], leg)
        bar(f"shin_{side:+}", knee, ankle, 0.066,
            mats["shirt"], leg)
        sphere(f"knee_panel_{side:+}", knee, (0.086, 0.072, 0.078),
               mats["detail"], leg, 16, 10)
        cube(f"boot_{side:+}", (0, -0.575, -0.390),
             (0.145, 0.245, 0.135), mats["dark"], leg, 0.045)
        cube(f"boot_stripe_{side:+}", (0, -0.660, -0.355),
             (0.150, 0.025, 0.030), mats["accent"], leg, 0.010)


def add_standard_driver_preview_context(mats):
    """Add a non-exported seat and wheel so the authored pose reads clearly."""
    seat_back = cube("PREVIEW_seat_back", (0, 0.115, -0.015),
                     (0.42, 0.10, 0.62), mats["dark"], bevel=0.065)
    seat_back.rotation_euler.x = math.radians(-8)
    seat_base = cube("PREVIEW_seat_base", (0, 0.035, -0.325),
                     (0.40, 0.44, 0.10), mats["dark"], bevel=0.045)
    wheel = torus("PREVIEW_steering_wheel", (0, -0.355, 0.105),
                  0.135, 0.016, mats["dark"],
                  rotation=(math.radians(68), 0, 0),
                  major_segments=20, minor_segments=6)
    column = bar("PREVIEW_steering_column", (0, -0.34, 0.09),
                 (0, -0.04, -0.10), 0.014, mats["metal"])
    for obj in (seat_back, seat_base, wheel, column):
        obj[ASSET_PROP] = False


def build_driver(slug: str):
    reset_scene()
    spec = DRIVERS[slug]
    mats = {
        "shirt": material(f"{slug}_shirt", spec["shirt"], roughness=0.44),
        "accent": material(f"{slug}_accent", spec["accent"], metallic=0.06, roughness=0.38),
        "detail": material(f"{slug}_detail", (0.82, 0.88, 0.84, 1),
                           metallic=0.04, roughness=0.46),
        "dark": material(f"{slug}_dark", (0.012, 0.016, 0.02, 1), roughness=0.62),
        "metal": material(f"{slug}_metal", (0.40, 0.45, 0.48, 1), metallic=0.72, roughness=0.22),
        "glass": material(f"{slug}_glass", (0.008, 0.018, 0.028, 1),
                          metallic=0.28, roughness=0.10),
        "gloves": material(f"{slug}_gloves", (0.010, 0.013, 0.018, 1),
                           roughness=0.52),
    }
    driver_root = empty("driver_root")
    driver_root["asset_id"] = f"formula_buggy.driver.{slug}"
    driver_root["attach_to"] = "seat_anchor"
    root = empty("root", owner=driver_root)
    torso = empty("torso", (0, 0, 0.12), root)
    head = empty("head", (0, -0.02, 0.47), root)
    arm_x = 0.28
    arm_l = empty("arm_L", (-arm_x, -0.02, 0.25), root)
    arm_r = empty("arm_R", (arm_x, -0.02, 0.25), root)
    leg_l = empty("leg_L", (-0.145, 0, -0.08), root)
    leg_r = empty("leg_R", (0.145, 0, -0.08), root)

    make_standard_driver(torso, head, arm_l, arm_r, leg_l, leg_r, mats)

    bones = {
        "driver_root_bone": {"head": (0, 0, 0), "tail": (0, 0, 0.18)},
        "torso_bone": {"head": (0, 0, 0.05), "tail": (0, 0, 0.38), "parent": "driver_root_bone"},
        "head_bone": {"head": (0, -0.02, 0.38), "tail": (0, -0.02, 0.61), "parent": "torso_bone"},
        "arm_L_bone": {"head": (-arm_x, -0.02, 0.25), "tail": (-arm_x - 0.07, -0.22, 0.10), "parent": "torso_bone"},
        "arm_R_bone": {"head": (arm_x, -0.02, 0.25), "tail": (arm_x + 0.07, -0.22, 0.10), "parent": "torso_bone"},
        "leg_L_bone": {"head": (-0.145, 0, -0.08), "tail": (-0.145, -0.30, -0.22), "parent": "driver_root_bone"},
        "leg_R_bone": {"head": (0.145, 0, -0.08), "tail": (0.145, -0.30, -0.22), "parent": "driver_root_bone"},
    }

    def group_for_object(obj):
        current = obj
        while current:
            mapping = {"head": "head_bone", "arm_L": "arm_L_bone", "arm_R": "arm_R_bone",
                       "leg_L": "leg_L_bone", "leg_R": "leg_R_bone", "torso": "torso_bone"}
            if current.name in mapping:
                return mapping[current.name]
            current = current.parent
        return "driver_root_bone"

    rig = build_rigid_rig("driver_rig", bones, asset_objects(), driver_root,
                          group_for_object)
    create_rig_action(rig, "idle", (1, 32), [
        {"bone": "torso_bone", "path": "location", "index": 2,
         "keys": [(1, 0), (16, 0.008), (32, 0)]},
        {"bone": "head_bone", "index": 2,
         "keys": [(1, math.radians(-1)), (16, math.radians(1)), (32, math.radians(-1))]},
    ])
    create_rig_action(rig, "accelerate", (40, 54), [
        {"bone": "torso_bone", "index": 0,
         "keys": [(40, 0), (47, math.radians(5)), (54, 0)]},
        {"bone": "head_bone", "index": 0,
         "keys": [(40, 0), (47, math.radians(-3)), (54, 0)]},
    ])
    create_rig_action(rig, "brake", (60, 74), [
        {"bone": "torso_bone", "index": 0,
         "keys": [(60, 0), (67, math.radians(-7)), (74, 0)]},
        {"bone": "head_bone", "index": 0,
         "keys": [(60, 0), (67, math.radians(4)), (74, 0)]},
    ])
    for clip, sign in (("turn_left", 1), ("turn_right", -1)):
        create_rig_action(rig, clip, (80, 100), [
            {"bone": "torso_bone", "index": 1,
             "keys": [(80, 0), (90, sign * math.radians(4)), (100, 0)]},
            {"bone": "head_bone", "index": 2,
             "keys": [(80, 0), (90, sign * math.radians(10)), (100, 0)]},
            {"bone": "arm_L_bone", "index": 2,
             "keys": [(80, 0), (90, sign * math.radians(12)), (100, 0)]},
            {"bone": "arm_R_bone", "index": 2,
             "keys": [(80, 0), (90, sign * math.radians(12)), (100, 0)]},
        ])
    # A common compact seated envelope keeps every silhouette compatible with
    # the same vehicle seat anchor while preserving proportions.
    driver_root.scale = (0.82, 0.82, 0.82)
    add_standard_driver_preview_context(mats)
    return spec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", choices=["all", *DRIVERS], default="all")
    parser.add_argument("--output-root", type=Path,
                        default=Path(__file__).resolve().parents[3] / "assets_src" / "drivers")
    args = parser.parse_args()
    targets = DRIVERS if args.asset == "all" else [args.asset]
    for slug in targets:
        spec = build_driver(slug)
        metadata = {
            "type": "driver",
            "display_name": spec["display_name"],
            "silhouette": spec["silhouette"],
            "design_style": "standard helmeted human",
            "target_seated_pose_height_m": 1.1,
            "target_dimensions_m": {"width_x": 0.65, "depth_y": 0.66,
                                    "seated_height_z": 1.1},
            "attachment": {"driver_origin": "pelvis", "vehicle_bone": "seat_anchor"},
            "animation_clips": {"idle": [1, 32], "accelerate": [40, 54],
                                "brake": [60, 74], "turn_left": [80, 100],
                                "turn_right": [80, 100]},
        }
        camera = (2.15, -3.15, 1.55)
        target = (0, -0.12, 0.08)
        export_asset(args.output_root / slug, slug, metadata, REQUIRED,
                     camera, target)


if __name__ == "__main__":
    main()
