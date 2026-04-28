from __future__ import annotations


def test_health_service_components_and_swim_warning(health_service, swim_store):
    health = health_service.check_all()
    assert health.status in {"ok", "warning"}
    assert health.status != "error"
    names = {component.name for component in health.components}
    assert {
        "operations",
        "narwhal",
        "hotstuff",
        "swim",
        "faults",
        "checkpointing",
        "recovery",
        "crypto",
    } <= names
    swim_component = next(component for component in health.components if component.name == "swim")
    assert swim_component.status == "warning"
    swim_store.bootstrap_from_config(1, "http://node1:8000", ["http://node2:8000"])
    health = health_service.check_all()
    swim_component = next(component for component in health.components if component.name == "swim")
    assert swim_component.details["alive"] == 2
