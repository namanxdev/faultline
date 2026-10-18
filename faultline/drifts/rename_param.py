"""rename_param: a parameter name changes in arguments, schemas, and nested results."""

from dataclasses import replace

from faultline.drifts.base import Drift, ToolFailure


class RenameParam(Drift):
    name = "rename_param"
    rationale = "APIs rename fields between versions; agents must read the live schema."

    def specs(self, service, specs):
        renames = service.RENAMES
        changed = []
        for s in specs:
            new = [renames[p.name] for p in s.params if p.name in renames]
            changed.append(
                replace(
                    s,
                    params=tuple(replace(p, name=renames.get(p.name, p.name)) for p in s.params),
                    description=s.description + "".join(f" Use {n}." for n in new),
                )
            )
        return changed

    def before(self, service, name, args):
        for old, new in service.RENAMES.items():
            if any(p.name == old for p in service.spec(name).params):
                if old in args or new not in args:
                    raise ToolFailure(f"Parameter changed: use {new} instead of {old}")
                args[old] = args.pop(new)
        return args

    def after(self, service, name, args, result):
        return rename(result, service.RENAMES)


def rename(value, renames: dict):
    if isinstance(value, dict):
        return {renames.get(k, k): rename(v, renames) for k, v in value.items()}
    if isinstance(value, list):
        return [rename(v, renames) for v in value]
    return value


DRIFT = RenameParam()
