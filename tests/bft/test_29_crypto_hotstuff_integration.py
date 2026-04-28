from __future__ import annotations

from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftSignedMessage
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.narwhal.service import NarwhalService


def test_hotstuff_proposal_vote_signatures_and_qc(
    operation_store,
    event_log,
    narwhal_store,
    hotstuff_store,
    crypto_service,
    sample_operation_input,
):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    hotstuff = HotStuffService(
        operation_store,
        event_log,
        narwhal_store,
        hotstuff_store,
        crypto_service=crypto_service,
    )
    operation = operation_store.create(sample_operation_input)
    batch = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 1).batch
    narwhal.certify_batch_locally(batch.batch_id, 6)
    proposal = hotstuff.create_proposal_from_batch(batch.batch_id, 1, 6)
    hotstuff.vote(proposal.proposal_id, 1, total_nodes=6)

    proposal_event = next(event for event in event_log.list() if event.message == "hotstuff_proposal_created")
    vote_event = next(event for event in event_log.list() if event.message == "hotstuff_vote_recorded")
    assert proposal_event.details["signed_message_id"]
    assert vote_event.details["signed_message_id"]
    assert crypto_service.verify_message_for_protocol(
        BftSignedMessage.model_validate(proposal_event.details["signed_message"]),
        ProtocolName.HOTSTUFF,
        MessageKind.PROPOSAL,
    ).valid
    vote_message = BftSignedMessage.model_validate(vote_event.details["signed_message"])
    assert crypto_service.verify_message_for_protocol(
        vote_message,
        ProtocolName.HOTSTUFF,
        MessageKind.VOTE,
    ).valid
    replay = crypto_service.verify_message(vote_message)
    assert replay.replay is True
    assert len(hotstuff_store.get_votes(proposal.proposal_id)) == 1
    bad_vote = vote_message.model_copy(update={"signature_b64": "bad"})
    assert crypto_service.verify_message(bad_vote, mark_seen=False).reason == "invalid_signature"
    qc = hotstuff.form_qc_demo(proposal.proposal_id, 6)
    assert qc.valid is True
