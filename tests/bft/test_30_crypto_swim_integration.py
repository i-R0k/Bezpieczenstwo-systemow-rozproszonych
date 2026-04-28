from __future__ import annotations

from vetclinic_api.bft.common.types import MessageKind, NodeStatus, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftSignedMessage
from vetclinic_api.bft.swim.models import SwimGossipUpdate
from vetclinic_api.bft.swim.service import SwimService


def test_swim_ping_ack_gossip_are_signed(swim_store, event_log, crypto_service):
    service = SwimService(swim_store, event_log, crypto_service=crypto_service)
    service.bootstrap(1, "http://node1:8000", ["http://node2:8000"])
    service.ping(1, 2)
    ping_event = next(event for event in event_log.list() if event.message == "swim_ping_ack")
    assert ping_event.details["signed_ping_message_id"]
    assert ping_event.details["signed_ack_message_id"]
    assert crypto_service.verify_message_for_protocol(
        BftSignedMessage.model_validate(ping_event.details["signed_ping_message"]),
        ProtocolName.SWIM,
        MessageKind.SWIM_PING,
    ).valid

    service.gossip(
        1,
        [SwimGossipUpdate(node_id=2, status=NodeStatus.SUSPECT, incarnation=1, observed_by=1)],
    )
    gossip_event = next(event for event in event_log.list() if event.message == "swim_gossip_applied")
    gossip_message = BftSignedMessage.model_validate(gossip_event.details["signed_gossip_message"])
    assert crypto_service.verify_message_for_protocol(
        gossip_message,
        ProtocolName.SWIM,
        MessageKind.SWIM_GOSSIP,
    ).valid
    assert crypto_service.verify_message(
        gossip_message.model_copy(update={"signature_b64": "bad"}),
        mark_seen=False,
    ).reason == "invalid_signature"
