"""BFT architecture boundary package."""

from __future__ import annotations

import inspect

import starlette.routing


def apply_fastapi_compat() -> None:
    """Patch older Starlette Router builds used with newer FastAPI."""

    if getattr(starlette.routing.Router, "_bft_compat_applied", False):
        return

    if "on_startup" not in inspect.signature(starlette.routing.Router.__init__).parameters:
        original_init = starlette.routing.Router.__init__

        def router_init_compat(self, *args, **kwargs):
            kwargs.pop("on_startup", None)
            kwargs.pop("on_shutdown", None)
            kwargs.pop("lifespan", None)
            original_init(self, *args, **kwargs)
            self.on_startup = getattr(self, "on_startup", [])
            self.on_shutdown = getattr(self, "on_shutdown", [])

        starlette.routing.Router.__init__ = router_init_compat

    starlette.routing.Router._bft_compat_applied = True
