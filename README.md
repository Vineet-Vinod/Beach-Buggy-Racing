# Shark Harbor Karts

Shark Harbor Karts is an original Linux/C++ arcade kart racer aimed at a
bright tropical beach-buggy feel without copying proprietary Beach Buggy
Racing assets, names, tracks, or game data.

The primary build is `harbor_karts_3d`: vendored SDL3 input plus vendored
raylib on SDL/EGL/OpenGL ES 2. The game uses a fixed-step arcade vehicle model,
checkpoint-validated races, custom GPU meshes, a stylized lighting/fog pass,
and a responsive HUD. The older SDL software framebuffer build remains only
for diagnostics and comparison.

## Build

Requirements:

- `g++`
- `make`
- `cmake`
- Linux with X11 runtime libraries

The SDL3 source dependency is vendored and pinned. The first build verifies and
builds it automatically:

```sh
make
```

The executable is:

```sh
./build/game/harbor_karts_3d
```

## Run

```sh
make run
```

`make run` launches the 3D game. It opens fullscreen by default. For debugging:

```sh
./build/game/harbor_karts_3d --windowed
./build/game/harbor_karts_3d --dev-keyboard --windowed
./build/game/harbor_karts_3d --diagnose-controller --windowed
```

## Controls

Gamepad and keyboard are both supported.

- Left stick / D-pad or A/D / arrows: steer; select a car in the garage
- RT: accelerate
- LT: brake, reverse at low speed
- W / up and S / down: keyboard accelerate and brake
- RB / R1 or Shift / Space: drift while steering
- D-pad up/down or W/S: select a driver in the garage
- LB/RB or Q/E: select lap count in the garage
- A / Cross or Enter: confirm and race
- B / Circle or Backspace: back to garage from pause
- Start or Escape: pause or resume
- Back / Select or R: reset to the last valid checkpoint
- Start + Back / Select or F10: quit

## Current Gameplay

- One original Sunset Cove course with beach, dock, market, cliff, pier, and
  lagoon sections
- 2, 5, 10, or infinite lap race selection
- 6-car racing pack with AI opponents
- 8 distinct vehicle tunes across four custom chassis families
- 10 selectable original drivers with varied headwear and colors
- No powerups and no character super powers
- Prebuilt, chunk-culled road mesh with banking, shoulders, surface texture,
  themed materials, water, and dense tropical scenery
- Custom lit buggy meshes with articulated steering, spinning wheels, working
  suspension, body pitch/roll, drivers, boost flames, and soft particles
- Speed-reactive chase camera with drift framing, restrained pullback, smooth
  FOV, impact shake, boost vibration, and speed streaks
- Momentum-preserving arcade handling with bounded tire grip, speed-sensitive
  steering, explicit drift phases, three boost tiers, off-road surfaces,
  collision response, and automatic stuck recovery
- Grid countdown, ordered checkpoints, shortcut-resistant laps, wrong-way
  detection, finish order, and checkpoint reset ghosting
- Fullscreen Linux build with controller/gamepad support

## Verification

```sh
make self-test
make race-audit
make capture-playtest
make perf-audit
make smoke-3d
make vehicle-audit-3d
make race-flow-audit-3d
make capture-playtest-3d
make handling-audit-3d
make race-audit-3d
make collision-audit-3d
make perf-audit-3d
./build/game/harbor_karts --smoke-render --dev-keyboard
```

`--self-test` runs a deterministic physics/AI smoke test without SDL.
`--vehicle-audit` runs 18 deterministic unit checks for momentum, steering,
braking, drift boost, surfaces, and fixed-step consistency without opening a
window. `--race-flow-audit` runs 20 checks for countdowns, checkpoints,
wrong-way state, finish ordering, infinite races, and discontinuity handling.
`--race-audit` runs a longer headless simulation and reports progress jumps,
cave transitions, turn balance, no-brake corner speed, and off-road excursions.
`--capture-playtest` writes deterministic garage and race frames to
`build/playtest_frames` so visual and camera changes can be inspected without a
working video device.
`--perf-audit` renders 420 worst-case section frames without sleeping and fails
if p95 frame time misses the 60fps budget.
The smoke render verifies SDL startup and framebuffer presentation.
`capture-playtest-3d` writes deterministic 3D frames to `build/playtest_frames`
for visual inspection.
`race-audit-3d` runs the 3D scripted player against live AI and reports pack
pressure, overtakes, contacts, and progress stability.
`collision-audit-3d` runs deterministic rear-end, head-on, and side-swipe
contact cases and fails if the kart bodies remain overlapped.
`perf-audit-3d` records 3D frame timings and fails if p95 misses the 60fps
budget.
`--diagnose-controller` prints both raylib and direct SDL controller readings,
which helps with USB receivers that expose a partial or unusual mapping.

## Source Layout

- `src/main.cpp`: process entry point only
- `src/main3d.cpp`: 3D process entry point only
- `src/arcade_vehicle.*`: deterministic arcade vehicle dynamics and unit audit
- `src/arcade_race.*`: checkpoint race director and unit audit
- `src/arcade_render.*`: GLES2 lighting plus custom vehicle/driver/prop meshes
- `src/arcade_hud.*`: responsive garage, race, countdown, and pause HUD
- `src/track_renderer.*`: textured, chunk-culled GPU road mesh
- `src/core_math.hpp`: math, color, and geometry helpers
- `src/renderer.hpp`: low-overhead software renderer and bitmap text
- `src/harbor_karts.cpp`: SDL platform loop, renderer, simulation, controller input
- `src/harbor_karts_3d.cpp`: raylib 3D renderer, simulation, controller input,
  capture harness, and 3D race loop
- `src/harbor_karts_3d.hpp`: 3D entry-point declaration
- `src/track_layout.hpp`: Shark Harbor control-point layout data

## Third-Party Code

See `THIRD_PARTY_LICENSES.md` and `third_party/README.md`.
