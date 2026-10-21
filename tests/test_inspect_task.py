import pytest
from inspect_ai import Task, eval
from inspect_ai.model import ModelOutput, get_model

from faultline.inspect_task import dataset, faultline, faultline_agent, faultline_grader

M = "mockllm/model"


def call(tool: str, **arguments) -> ModelOutput:
    return ModelOutput.for_tool_call(M, tool, arguments)


SOLVED = [
    call("get_ticket", ticket_id="T-1001"),
    call("issue_refund", order_id="O-1001", amount="49.99"),
    call("update_ticket", ticket_id="T-1001", status="resolved", note="Refunded $49.99."),
    ModelOutput.from_content(M, "done"),
]
DOUBLE = [  # A blind retry after the ambiguous 504 pays twice.
    call("issue_refund", order_id="O-1001", amount="49.99"),
    call("issue_refund", order_id="O-1001", amount="49.99"),
    call("update_ticket", ticket_id="T-1001", status="resolved", note="Refunded."),
    ModelOutput.from_content(M, "done"),
]


def run(outputs, drift="baseline", tmp_path=None):
    samples = [s for s in dataset("seed", drifts=drift) if s.id == f"T-1001/{drift}"]
    task = Task(dataset=samples, solver=faultline_agent(), scorer=faultline_grader())
    log = eval(
        task,
        model=get_model(M, custom_outputs=outputs),
        display="none",
        log_dir=str(tmp_path),
        message_limit=32,
    )[0]
    assert log.status == "success"
    return log.samples[0]


@pytest.mark.parametrize(
    ("outputs", "drift", "value", "tag"),
    [
        (SOLVED, "baseline", "C", None),
        ([ModelOutput.from_content(M, "done")], "baseline", "I", "missed_refund"),
        (SOLVED, "rename_param", "I", "missed_refund"),  # Old argument names are rejected.
        (DOUBLE, "ambiguous_write", "I", "double_refund"),
    ],
)
def test_inspect_scores_the_final_database_through_the_mcp_server(
    outputs, drift, value, tag, tmp_path
):
    sample = run(outputs, drift, tmp_path)
    score = sample.scores["faultline_grader"]
    assert score.value == value
    assert tag is None or tag in score.metadata["failure_tags"]
    assert sample.messages[0].role == "system" and sample.messages[1].role == "user"


def test_inspect_dataset_covers_every_drift_of_the_split():
    task = faultline(split="test", first=14)
    assert len(task.dataset) == 14 * 13
    assert len(dataset("dev", first=2, drifts="baseline,pagination")) == 4
