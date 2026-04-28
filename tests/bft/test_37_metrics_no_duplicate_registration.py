from __future__ import annotations

import importlib

from vetclinic_api.bft.observability import metrics
from vetclinic_api.bft.observability.metrics import BftMetrics


def test_metrics_module_reload_and_multiple_instances_do_not_duplicate():
    importlib.reload(metrics)
    first = BftMetrics()
    second = BftMetrics()
    first.reset_for_tests()
    second.reset_for_tests()
    assert "bft_crypto_messages_signed_total" in first.export_latest_text()
    assert "bft_crypto_messages_signed_total" in second.export_latest_text()
