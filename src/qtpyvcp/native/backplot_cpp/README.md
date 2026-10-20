# QtPyVCP C++ backplot builder

`_backplot_cpp` parses a program through the native canon and returns plain
NumPy arrays (per-WCS points, colours, line numbers, offset transitions and
timing). It has no renderer dependency: both the Python fallback and the Qt
Quick 3D backplot consume the same payload.

## Build (manual, branch testing)

```bash
cd qtpyvcp/src/qtpyvcp/native/backplot_cpp
cmake -S . -B build
cmake --build build -j
```

The resulting extension module `_backplot_cpp` is located automatically by
`qtpyvcp.native.backplot_cpp.native_module`, preferring the newest build.

## Fallbacks

`backplot_common.loader` uses the Python canon when the native module is
unavailable, for foam/jet machines, or when the caller vetoes the native path
(e.g. table-rotary machines that need load-time rotary shaping).
