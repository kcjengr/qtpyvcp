#!/usr/bin/env python3

"""QNative - build QtPyVCP native modules

Usage:
  qnative
  qnative --widgets
  qnative --backplot
    qnative --build-root BUILD_ROOT
  qnative -h

Examples:
  qnative
  qnative --widgets
  qnative --backplot
    qnative --build-root /tmp/qnative-build
"""

from __future__ import annotations

import argparse
import glob
import shutil
import subprocess
import sys
from pathlib import Path


OK = "\033[32mok\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def _run(cmd: list[str], cwd: Path) -> int:
    print(f"$ {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(cwd))


def _copy_built_artifact(build_dir: Path, pattern: str, dest_dir: Path) -> bool:
    matches = sorted(glob.glob(str(build_dir / pattern)))
    if not matches:
        print(f"{FAIL} missing build artifact: {build_dir / pattern}")
        return False

    src = Path(matches[-1])
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    print(f"{OK} staged artifact: {dest}")
    return True


def _build_cmake_project(source_dir: Path, build_dir: Path, *, artifact_pattern: str | None = None, artifact_dest: Path | None = None) -> bool:
    if not (source_dir / "CMakeLists.txt").exists():
        print(f"{FAIL} missing CMakeLists.txt: {source_dir}")
        return False

    configure_cmd = ["cmake", "-S", str(source_dir), "-B", str(build_dir)]
    build_cmd = ["cmake", "--build", str(build_dir), "-j"]

    if _run(configure_cmd, cwd=source_dir.parent) != 0:
        print(f"{FAIL} configure failed: {source_dir}")
        return False

    if _run(build_cmd, cwd=source_dir.parent) != 0:
        print(f"{FAIL} build failed: {source_dir}")
        return False

    if artifact_pattern is not None and artifact_dest is not None:
        if not _copy_built_artifact(build_dir, artifact_pattern, artifact_dest):
            return False

    print(f"{OK} built: {source_dir}")
    return True


def _resolve_package_root(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg).resolve()
    return Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build QtPyVCP native modules")
    parser.add_argument("--widgets", action="store_true", help="Build C++ widgets plugin modules")
    parser.add_argument("--backplot", action="store_true", help="Build backplot C++ module")
    parser.add_argument(
        "--package-root",
        default=None,
        help="Path to qtpyvcp package root (contains native/). Defaults to current qtpyvcp package location.",
    )
    parser.add_argument(
        "--build-root",
        default=None,
        help="Optional external build directory root. Use this to avoid in-tree build/ directories.",
    )
    args = parser.parse_args()

    package_root = _resolve_package_root(args.package_root)
    native_root = package_root / "native"

    if not native_root.exists():
        print(f"{FAIL} native root not found: {native_root}")
        return 1

    build_widgets = args.widgets
    build_backplot = args.backplot

    # No flags means build everything native.
    if not build_widgets and not build_backplot:
        build_widgets = True
        build_backplot = True

    results: list[bool] = []
    build_root = Path(args.build_root).resolve() if args.build_root else None

    if build_widgets:
        widgets_src = native_root / "widgets_cpp" / "gcode_editor"
        widgets_build = (
            build_root / "widgets_cpp" / "gcode_editor"
            if build_root
            else widgets_src / "build"
        )
        results.append(
            _build_cmake_project(
                widgets_src,
                widgets_build,
                artifact_pattern="*gcodeeditorplugin*.so",
                artifact_dest=widgets_src,
            )
        )

    if build_backplot:
        backplot_src = native_root / "backplot_cpp"
        backplot_build = (
            build_root / "backplot_cpp"
            if build_root
            else backplot_src / "build"
        )
        results.append(
            _build_cmake_project(
                backplot_src,
                backplot_build,
                artifact_pattern="_backplot_cpp*.so",
                artifact_dest=backplot_src,
            )
        )

    if results and all(results):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
