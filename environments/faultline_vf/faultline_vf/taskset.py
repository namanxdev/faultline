"""faultline as a verifiers v1 taskset.

Each task is one faultline task under one drift. A per-rollout `Toolset` serves the
drifted faultline tools over MCP; the reward is the state grade of the final database,
plus optional shaping that can never let a failing episode beat a passing one.
"""

import tempfile
from functools import cache
from pathlib import Path

import verifiers.v1 as vf

from faultline import itsm, rewards
from faultline.db import TABLES, seed_rows, snapshot
from faultline.grader import Grade, grade_task
from faultline.llm import system_prompt, task_prompt
from faultline.runner import policy_version
from faultline.server import DOMAINS, _tool
from faultline.tasks import SPLIT_DRIFTS, load
from faultline.validate import episode


@cache
def _tasks(split: str) -> dict:
    return {t.task_id: t for t in load(split)}


class FaultlineState(vf.State):
    db: str = ""
    calls: list[str] = []
    """Names of tool calls that succeeded, in order (only for optional shaping)."""


class FaultlineData(vf.TaskData):
    task_id: str
    split: str
    drift: str
    domain: str


class FaultlineToolset(vf.Toolset[vf.ToolsetConfig, FaultlineState]):
    TOOL_PREFIX = None  # Publish the bare tool names, as faultline's own server does.

    async def setup_task(self, data: FaultlineData) -> None:
        # One server process per rollout, so this service's drift counters are per trial.
        self.service = DOMAINS[data.domain](Path("unset"), data.drift)

    def register(self, mcp) -> None:
        for spec in self.service.specs():
            mcp.add_tool(
                self._with_state(self._call(spec)), name=spec.name, description=spec.description
            )
        listed = mcp.list_tools

        async def list_tools():
            # Read descriptions per request, so description_drift changes them mid-rollout.
            current = {s.name: s.description for s in self.service.specs()}
            return [t.model_copy(update={"description": current[t.name]}) for t in await listed()]

        mcp.list_tools = list_tools

    def _call(self, spec):
        run = _tool(self.service, spec)

        def call(**args):
            self.service.path = Path(self.state.db)
            result = run(**args)
            self.state.calls = [*self.state.calls, spec.name]
            return result

        call.__signature__ = run.__signature__
        call.__name__ = spec.name
        return call


class FaultlineTaskConfig(vf.TaskConfig):
    tools: vf.ToolsetConfig = vf.ToolsetConfig()
    shaped: bool = False
    """Add the bounded shaping term from `faultline.rewards` to the reward."""


class FaultlineTask(vf.Task[FaultlineData, FaultlineState, FaultlineTaskConfig]):
    @classmethod
    def toolsets(cls, config: FaultlineTaskConfig) -> list[vf.Toolset]:
        return [FaultlineToolset(config.tools)]

    @property
    def faultline(self):
        return _tasks(self.data.split)[self.data.task_id]

    async def setup(self, trace: vf.Trace, runtime: vf.Runtime) -> None:
        db = Path(tempfile.mkdtemp(prefix="faultline-vf-")) / "state.sqlite3"
        seed_rows(db, self.faultline.schema, self.faultline.rows)
        trace.state.db = str(db)

    def _grade(self, db: str) -> Grade:
        task = self.faultline
        fresh = Path(tempfile.mkdtemp(prefix="faultline-vf-before-")) / "seed.sqlite3"
        seed_rows(fresh, task.schema, task.rows)
        before = snapshot(fresh, itsm.TABLES if task.domain == "itsm" else TABLES)
        return grade_task(before, db, task, policy_version(self.data.drift))

    @vf.reward
    async def solved(self, trace: vf.Trace) -> float:
        passed = self._grade(trace.state.db).passed
        version = policy_version(self.data.drift)
        return rewards.reward(
            passed, self.faultline, version, trace.state.calls, self.config.shaped
        )

    @vf.metric
    async def failure_tags(self, trace: vf.Trace) -> dict[str, float]:
        return {f"tag/{t}": 1.0 for t in self._grade(trace.state.db).failure_tags}

    async def validate(self, runtime: vf.Runtime) -> bool:
        # Gold check: the drift-robust oracle passes this task under this drift.
        result, error = await episode(self.faultline, self.data.drift, "oracle")
        return result.passed and error is None


class FaultlineTasksetConfig(vf.TasksetConfig):
    task: FaultlineTaskConfig = FaultlineTaskConfig()
    split: str = "train"
    notes: str = "stale"


class FaultlineTaskset(vf.Taskset[FaultlineTask, FaultlineTasksetConfig]):
    def load(self):
        split = self.config.split
        for task in _tasks(split).values():
            for drift in SPLIT_DRIFTS[split]:
                yield FaultlineTask(
                    FaultlineData(
                        id=f"{task.task_id}/{drift}",
                        name=f"{task.template}/{drift}",
                        prompt=task_prompt(task.target),
                        system_prompt=system_prompt(self.config.notes, task.domain),
                        task_id=task.task_id,
                        split=split,
                        drift=drift,
                        domain=task.domain,
                    ),
                    self.config.task,
                )


if __name__ == "__main__":
    # verifiers launches each rollout's tool server as `python -m faultline_vf.taskset`.
    FaultlineToolset.run()
