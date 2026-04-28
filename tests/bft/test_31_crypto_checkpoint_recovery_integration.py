from __future__ import annotations

from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftSignedMessage
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.narwhal.service import NarwhalService


def _committed(operation_store, event_log, narwhal_store, hotstuff_store, sample_input):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    hotstuff = HotStuffService(operation_store, event_log, narwhal_store, hotstuff_store)
    operation = operation_store.create(sample_input)
    batch = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 1).batch
    narwhal.certify_batch_locally(batch.batch_id, 6)
    hotstuff.run_hotstuff_demo_for_operation(operation.operation_id, 1, 6)


def test_checkpoint_and_recovery_are_signed(
    operation_store,
    event_log,
    narwhal_store,
    hotstuff_store,
    checkpoint_service,
    recovery_service,
    swim_store,
    crypto_service,
    sample_operation_input,
):
    checkpoint_service.crypto_service = crypto_service
    recovery_service.crypto_service = crypto_service
    _committed(operation_store, event_log, narwhal_store, hotstuff_store, sample_operation_input)
    snapshot = checkpoint_service.create_snapshot(1)
    certificate = checkpoint_service.certify_snapshot(snapshot.snapshot_id, 6)
    checkpoint_event = next(event for event in event_log.list() if event.message == "checkpoint_certificate_formed")
    checkpoint_message = BftSignedMessage.model_validate(checkpoint_event.details["signed_messages"][0])
    assert crypto_service.verify_message_for_protocol(
        checkpoint_message,
        ProtocolName.CHECKPOINTING,
        MessageKind.CHECKPOINT,
    ).valid

    swim_store.bootstrap_from_config(1, "http://node1:8000", ["http://node2:8000"])
    request = recovery_service.request_state_transfer(2, certificate.checkpoint_id)
    response = recovery_service.build_state_transfer_response(request)
    request_event = next(event for event in event_log.list() if event.message == "state_transfer_requested")
    request_message = BftSignedMessage.model_validate(request_event.details["signed_message"])
    assert crypto_service.verify_message_for_protocol(
        request_message,
        ProtocolName.RECOVERY,
        MessageKind.STATE_TRANSFER,
    ).valid
    assert crypto_service.verify_message(
        request_message.model_copy(update={"signature_b64": "bad"}),
        mark_seen=False,
    ).reason == "invalid_signature"
    result = recovery_service.apply_state_transfer(request)
    assert result.status == "RECOVERED"
    assert response.state_hash == result.applied_state_hash
