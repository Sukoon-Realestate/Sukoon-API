import asyncio
from unittest.mock import patch

import pytest

from core_apps.virtual_tours import runtime, tasks


@pytest.mark.parametrize(
    "mode,starts", [("inline", True), ("celery", False), ("polling", False)]
)
def test_asgi_lifespan_starts_only_explicit_inline_processor_and_stops(
    settings, mode, starts
):
    settings.VIRTUAL_TOUR_PROCESSOR_MODE = mode
    messages = iter([{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}])
    sent = []

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    with patch.object(runtime, "run_processor") as processor:
        asyncio.run(runtime.lifespan({"type": "lifespan"}, receive, send))
    assert processor.called == starts
    if starts:
        processor.assert_called_once()
        assert processor.call_args.args[0].is_set()
    assert sent == [
        {"type": "lifespan.startup.complete"},
        {"type": "lifespan.shutdown.complete"},
    ]


def test_inline_dispatch_uses_durable_queue(settings):
    settings.VIRTUAL_TOUR_PROCESSOR_MODE = "inline"
    with patch.object(tasks.process_tour, "delay") as dispatch:
        tasks.dispatch_revision("revision", "hash")
    dispatch.assert_not_called()
