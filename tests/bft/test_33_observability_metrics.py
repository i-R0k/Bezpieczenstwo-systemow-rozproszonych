from __future__ import annotations

import uuid

from vetclinic_api.bft.common.events import ProtocolEvent
from vetclinic_api.bft.common.types import ProtocolName
from vetclinic_api.bft.observability.metrics import BftMetrics


def test_bft_metrics_record_events_and_export(bft_metrics, narwhal_store, hotstuff_store):
    text = bft_metrics.export_latest_text()
    assert "bft_narwhal_batches_created_total" in text

    bft_metrics.record_event(
        ProtocolEvent(
            event_id=str(uuid.uuid4()),
            protocol=ProtocolName.NARWHAL,
            message="batch_created",
        )
    )
    bft_metrics.record_event(
        ProtocolEvent(
            event_id=str(uuid.uuid4()),
            protocol=ProtocolName.HOTSTUFF,
            message="hotstuff_block_committed",
        )
    )
    snapshot = bft_metrics.snapshot()
    assert snapshot["counters"]["bft_narwhal_batches_created_total"] == 1
    assert snapshot["counters"]["bft_hotstuff_commits_total"] == 1
    gauges = bft_metrics.refresh_gauges(narwhal_store=narwhal_store, hotstuff_store=hotstuff_store)
    assert isinstance(gauges, dict)


def test_bft_metrics_no_duplicate_registration():
    first = BftMetrics()
    second = BftMetrics()
    first.reset_for_tests()
    second.reset_for_tests()
    assert "bft_operations_submitted_total" in first.export_latest_text()
