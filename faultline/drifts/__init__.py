"""Perturbations, one module each. A combined drift joins two names with "+"."""

from faultline.drifts import (
    ambiguous_write,
    description_drift,
    pagination,
    policy_v4,
    rate_limit_429,
    rename_param,
    transient_503,
)
from faultline.drifts.base import Drift, ToolFailure
from faultline.drifts.combined import COMBINED, HELD_OUT

SINGLE = {
    d.name: d
    for d in (
        Drift(),
        rename_param.DRIFT,
        transient_503.DRIFT,
        ambiguous_write.DRIFT,
        rate_limit_429.DRIFT,
        pagination.DRIFT,
        description_drift.DRIFT,
        policy_v4.DRIFT,
    )
}
PHASE1_DRIFTS = ("baseline", "rename_param", "transient_503", "ambiguous_write")
DRIFTS = (*SINGLE, *COMBINED)
TRAIN_DRIFTS = tuple(d for d in DRIFTS if d not in HELD_OUT)

__all__ = ["COMBINED", "DRIFTS", "HELD_OUT", "PHASE1_DRIFTS", "TRAIN_DRIFTS", "ToolFailure"]


def parse(name: str) -> tuple[Drift, ...]:
    if name not in DRIFTS:
        raise ValueError(f"Unknown drift: {name}")
    return tuple(SINGLE[part] for part in name.split("+"))
