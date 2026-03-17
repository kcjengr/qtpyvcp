# VTK Backplot Ownership Skeleton (Reference Only)

This folder is a reference scaffold only.

- It is not imported by runtime code.
- It documents how to drive VTK behavior from axis ownership.
- Canonical ownership terms are `head` and `table`.
- Legacy term `tool` is treated as alias to `head`.

## Intended flow

1. Parse and normalize axis owners from INI.
2. Build a compact ownership signature (for logs/debug).
3. Resolve plotting behavior policy from ownership and runtime state.
4. Apply that policy in existing runtime files:
   - `linuxcnc_datasource.py`
   - `vtk_backplot.py`
   - `vtk_canon.py`

## Ownership signature examples

- `xyz_hhh` -> all linear axes head-owned.
- `xyz_tth` -> X and Y table-owned, Z head-owned.
- `xyzac_tthtt` -> XYZAC mix, useful for trunnion-style machines.

Use this scaffold as a design guide while implementing in existing files.
