"""Reference-only scaffold for deriving plot behavior from ownership.

Not imported by runtime.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlotBehaviorPolicy:
    # Where live breadcrumb points are stored.
    # - "path" means follow active path transform.
    # - "world" means fixed in world coordinates.
    breadcrumb_frame: str

    # Whether table-rotary path sampling is needed for preview.
    enable_table_rotary_sampling: bool

    # Whether to use table-aware joint-backed linear position for runtime traces.
    enable_table_linear_joint_feedback: bool


def derive_policy(owners: dict, switchkins_type: int) -> PlotBehaviorPolicy:
    """Derive behavior from ownership and runtime state.

    This is the core idea: rule-based composition from axis ownership,
    not per-machine hardcoded branches.
    """
    has_table_linear = any(owners.get(a) == "table" for a in ("X", "Y", "Z"))
    has_table_rotary = any(owners.get(a) == "table" for a in ("A", "B", "C"))

    if has_table_linear or has_table_rotary:
        breadcrumb_frame = "path"
    else:
        breadcrumb_frame = "world"

    return PlotBehaviorPolicy(
        breadcrumb_frame=breadcrumb_frame,
        enable_table_rotary_sampling=has_table_rotary,
        enable_table_linear_joint_feedback=has_table_linear,
    )
