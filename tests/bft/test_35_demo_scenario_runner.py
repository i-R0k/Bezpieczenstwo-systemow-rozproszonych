from __future__ import annotations


def test_demo_scenario_runner_full_flow(demo_runner):
    report = demo_runner.run_full_demo(total_nodes=6)
    assert report.status == "ok"
    assert report.final_operation_status == "EXECUTED"
    assert report.checkpoint_id is not None
    assert report.recovered_node_id == 3
    assert report.errors == []
    assert report.metrics_snapshot
    step_names = {step.name for step in report.steps}
    assert {
        "Bootstrap",
        "Submit operation",
        "Narwhal",
        "HotStuff",
        "Execute",
        "Fault injection",
        "Checkpoint",
        "Recovery",
        "Crypto verification",
        "Health after",
    } <= step_names
