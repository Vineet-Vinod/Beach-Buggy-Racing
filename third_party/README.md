# Third-Party Dependencies

The game vendors only source release archives that are needed to produce the
Linux executable on this machine. Generated build trees stay under `build/`.

## Vendored Archives

- `SDL3-3.4.10.tar.gz`
  - Source: `https://github.com/libsdl-org/SDL/releases/download/release-3.4.10/SDL3-3.4.10.tar.gz`
  - SHA-256: `12b34280415ec8418c864408b93d008a20a6530687ee613d60bfbd20411f2785`
  - Purpose: windowing, fullscreen, controller/gamepad input, timing.
- `libXext-1.3.6.tar.xz`
  - Source: `https://www.x.org/releases/individual/lib/libXext-1.3.6.tar.xz`
  - SHA-256: `edb59fa23994e405fdc5b400afdf5820ae6160b94f35e3dc3da4457a16e89753`
  - Purpose: headers needed by SDL's X11 backend on this laptop.

## Rebuilding

```sh
scripts/bootstrap_deps.sh
```

The script verifies both archive checksums, extracts them into `build/deps/src`,
builds static SDL3, and installs it into `build/deps/install`.

No proprietary Beach Buggy Racing assets, names, tracks, character art, or
game data are vendored here.
