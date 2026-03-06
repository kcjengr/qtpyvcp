# QtPyVCP C++ Backplot Bridge (Scaffold)

This directory contains the initial scaffold for a native C++ backplot builder.

## Current state

- Python bridge exists in `bridge.py`.
- Native entrypoint is `_backplot_cpp.build_from_canon(...)`.
- Current C++ implementation builds non-foam geometry payload (points/colors/segments + transitions) directly from canon/path data and returns timing.
- Runtime integration in `vtk_backplot.py` safely falls back to the Python draw path when native is unavailable or raises.
- Foam mode currently falls back to Python path.

## Build (manual, branch testing)

```bash
cd qtpyvcp/src/qtpyvcp/native/backplot_cpp
cmake -S . -B build
cmake --build build -j
```

The resulting extension module `_backplot_cpp` should be placed on the Python import path within this package for runtime use.

## Next implementation target

Complete parity and deeper offload:

- `path_actors`: per-WCS path actor objects compatible with existing pipeline.
- `offset_transitions`: transition structures consumed by current transition rendering.
- `added_segments`: integer count for perf summary.
- `draw_ms`: C++ draw/build elapsed time in ms.
- Add foam path support.
- Move VTK object construction to pure C++ extension output for additional overhead reduction.
