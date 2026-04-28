from __future__ import annotations

from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftMessagePayload
from vetclinic_api.bft.crypto.keys import generate_node_keypair


def _payload(protocol=ProtocolName.HOTSTUFF, kind=MessageKind.VOTE):
    return BftMessagePayload(
        protocol=protocol,
        message_kind=kind,
        source_node_id=1,
        body={"ok": True},
    )


def test_crypto_service_verify_replay_and_rejections(
    crypto_service,
    node_key_registry,
    event_log,
):
    crypto_service.ensure_demo_keys(2)
    message = crypto_service.sign_message(_payload(), 1)
    assert crypto_service.verify_message(message).valid is True
    replay = crypto_service.verify_message(message)
    assert replay.valid is False
    assert replay.replay is True
    assert crypto_service.verify_message(message, mark_seen=False).valid is True

    changed_key = generate_node_keypair(99)
    mismatch = message.model_copy(update={"public_key_b64": changed_key.public_key_b64})
    assert crypto_service.verify_message(mismatch, mark_seen=False).reason == "public_key_mismatch"

    bad_sig = message.model_copy(update={"signature_b64": changed_key.public_key_b64})
    assert crypto_service.verify_message(bad_sig, mark_seen=False).reason == "invalid_signature"
    assert crypto_service.verify_message_for_protocol(
        message,
        ProtocolName.NARWHAL,
    ).reason == "protocol_mismatch"
    assert crypto_service.verify_message_for_protocol(
        message,
        ProtocolName.HOTSTUFF,
        MessageKind.PROPOSAL,
    ).reason == "message_kind_mismatch"
    messages = {event.message for event in event_log.list()}
    assert {"bft_message_signed", "bft_message_verified", "bft_message_rejected"} <= messages
