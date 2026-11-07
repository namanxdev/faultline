# Lazy export: verifiers starts the toolset with `python -m faultline_vf.taskset`, so
# importing the package must not import that module first.
__all__ = ["FaultlineTaskset"]


def __getattr__(name: str):
    if name == "FaultlineTaskset":
        from faultline_vf.taskset import FaultlineTaskset

        return FaultlineTaskset
    raise AttributeError(name)
