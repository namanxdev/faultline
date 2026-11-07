# faultline-vf

[faultline](https://github.com/namanxdev/faultline) as a verifiers v1 taskset. It is an
RL training and evaluation environment for tool-using agents whose MCP tools **drift**
while they work: a parameter is renamed, a description changes, and the agent must
notice and adapt.

- **Task.** One faultline task under one drift. Each rollout gets a fresh SQLite
  database and its own MCP server process, which serves the drifted tools.
- **Reward.** `solved` is the grade of the final database state against the policy
  text. The grader never reads the transcript. Optional bounded shaping is available
  with `--env.taskset.task.shaped true`.
- **Gold check.** The `validate` hook runs the oracle agent, which must solve every
  task under every drift.
- **Splits.** `train` (default), `dev`, and `test`, set with `--taskset.split`.

## Usage

verifiers imports `fcntl`, so this runs on Linux and macOS, not Windows.

```sh
prime env install naman411/faultline-vf
uv run vf-validate faultline-vf --taskset.split dev --select.limit 26 --runtime.type subprocess
```

The package depends on `faultline`, which is not on a package index. To run from
source, clone the repository and work in `environments/faultline_vf`:

```sh
git clone https://github.com/namanxdev/faultline
cd faultline/environments/faultline_vf
uv sync
uv run vf-validate faultline-vf --taskset.split dev --select.limit 26 --runtime.type subprocess
uv run vf-eval @ configs/smoke.toml -n 4 -r 1 --no-push   # needs OPENROUTER_API_KEY
```

## Recorded results

- `vf-validate` on `dev`, 26 tasks: gold and noop were both valid 26/26.
- 4 rollouts of Haiku 5.5 with the `null` harness (task tools only, no shell) all
  scored reward 1.00, for $0.0065. This is a smoke test, not a benchmark.

## Notes

The package overrides `mcp` to 2.0.0, which verifiers 0.4.0 pins. faultline itself pins
2.3.0. The taskset uses only faultline's tools, drifts, tasks, and grader, which pass
faultline's suite on mcp 2.0.0 except for faultline's own stdio runner, which this
package does not use.
