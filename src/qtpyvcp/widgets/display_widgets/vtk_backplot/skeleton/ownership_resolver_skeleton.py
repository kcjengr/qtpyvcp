"""Reference-only scaffold for axis ownership normalization.

Not imported by runtime.
"""

from dataclasses import dataclass

AXES = ("X", "Y", "Z", "A", "B", "C")


@dataclass(frozen=True)
class OwnershipConfig:
    owners: dict
    source: str


def normalize_owner(raw_value: str | None) -> str:
    """Return canonical owner name: 'head' or 'table'.

    Legacy alias mapping:
    - 'tool' -> 'head'
    """
    text = (raw_value or "").strip().lower()
    if text == "tool":
        return "head"
    if text in ("head", "table"):
        return text
    return "head"


def resolve_owners(inifile) -> OwnershipConfig:
    """Resolve ownership map from INI with defaults.

    Defaults:
    - X/Y/Z/A/B/C default to 'head'
    """
    owners = {}
    used_explicit = False
    for axis in AXES:
        raw = inifile.find("VTK", axis)
        owner = normalize_owner(raw)
        owners[axis] = owner
        if raw is not None:
            used_explicit = True

    source = "explicit" if used_explicit else "default"
    return OwnershipConfig(owners=owners, source=source)


def make_signature(owners: dict, axes: tuple[str, ...]) -> str:
    """Build a compact signature like 'xyzac_tthtt'."""
    prefix = "".join(a.lower() for a in axes)
    bits = "".join("t" if owners.get(a) == "table" else "h" for a in axes)
    return f"{prefix}_{bits}"
