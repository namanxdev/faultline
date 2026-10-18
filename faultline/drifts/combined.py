"""combined: two drifts at once, written "a+b". Some pairs are held out of the train split."""

COMBINED = (
    "rename_param+transient_503",
    "transient_503+ambiguous_write",
    "pagination+rate_limit_429",
    "rename_param+ambiguous_write",
    "policy_v4+description_drift",
)
# Never used in train, so dev and test measure generalization to unseen combinations.
HELD_OUT = ("rename_param+ambiguous_write", "policy_v4+description_drift")
