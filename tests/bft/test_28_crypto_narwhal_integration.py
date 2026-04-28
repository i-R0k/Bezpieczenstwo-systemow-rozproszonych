from __future__ import annotations

from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftSignedMessage
from vetclinic_api.bft.narwhal.service import NarwhalService


def test_narwhal_batch_and_ack_are_signed(
    operation_store,
    event_log,
    narwhal_store,
    crypto_service,
    sample_operation_input,
):
    service = NarwhalService(operation_store, event_log, narwhal_store, crypto_service=crypto_service)
    operation = operation_store.create(sample_operation_input)
    response = service.create_batch_from_operations(1, 6, [operation.operation_id], 1)
    service.acknowledge_batch(response.batch.batch_id, 2, total_nodes=6)
    signed_events = [event for event in event_log.list() if "signed_message_id" in event.details]
    assert signed_events
    batch_signed = next(event for event in event_log.list() if event.message == "narwhal_batch_signed")
    verified = crypto_service.verify_message_for_protocol(
        BftSignedMessage.model_validate(batch_signed.details["signed_message"]),
        ProtocolName.NARWHAL,
        MessageKind.BATCH,
    )
    assert verified.valid is True
    service.acknowledge_batch(response.batch.batch_id, 2, total_nodes=6)
    vertex = narwhal_store.get_dag().vertices[0]
    assert vertex.ack_node_ids.count(2) == 1
