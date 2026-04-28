from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.mark.bft
@pytest.mark.integration
def test_full_fastapi_app_imports_and_exposes_bft_routes():
    main = importlib.import_module("vetclinic_api.main")
    assert hasattr(main, "app")

    paths = {route.path for route in main.app.routes}
    assert "/bft/architecture" in paths
    assert "/bft/protocols" in paths
    assert "/bft/quorum" in paths

    client = TestClient(main.app)
    response = client.get("/bft/architecture")
    assert response.status_code == 200
