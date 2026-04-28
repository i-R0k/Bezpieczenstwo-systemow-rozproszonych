from __future__ import annotations

import uuid

from vetclinic_api.bft.common.events import EventLog, ProtocolEvent
from vetclinic_api.bft.common.operations import InMemoryOperationStore
from vetclinic_api.bft.common.types import (
    MessageKind,
    NodeStatus,
    OperationStatus,
    ProtocolName,
)
from vetclinic_api.bft.crypto.envelope import BftMessagePayload
from vetclinic_api.bft.crypto.service import CryptoService
from vetclinic_api.bft.fault_injection.equivocation import EQUIVOCATION_DETECTOR
from vetclinic_api.bft.fault_injection.models import FaultEvaluationContext
from vetclinic_api.bft.fault_injection.replay import REPLAY_GUARD
from vetclinic_api.bft.fault_injection.service import FaultInjectionService
from vetclinic_api.bft.hotstuff.models import (
    CommitCertificate,
    HotStuffBlock,
    HotStuffProposal,
    HotStuffStatus,
    HotStuffVote,
    QuorumCertificate,
    TimeoutCertificate,
    TimeoutVote,
    ViewState,
)
from vetclinic_api.bft.hotstuff.store import (
    InMemoryHotStuffStore,
    build_block_id,
    stable_hash,
)
from vetclinic_api.bft.narwhal.store import InMemoryNarwhalStore
from vetclinic_api.bft.swim.store import InMemorySwimStore


class HotStuffService:
    def __init__(
        self,
        operation_store: InMemoryOperationStore,
        event_log: EventLog,
        narwhal_store: InMemoryNarwhalStore,
        hotstuff_store: InMemoryHotStuffStore,
        swim_store: InMemorySwimStore | None = None,
        fault_service: FaultInjectionService | None = None,
        crypto_service: CryptoService | None = None,
    ) -> None:
        self.operation_store = operation_store
        self.event_log = event_log
        self.narwhal_store = narwhal_store
        self.hotstuff_store = hotstuff_store
        self.swim_store = swim_store
        self.fault_service = fault_service
        self.crypto_service = crypto_service

    def create_proposal_from_batch(
        self,
        batch_id: str,
        proposer_node_id: int,
        total_nodes: int,
    ) -> HotStuffProposal:
        del total_nodes
        self._ensure_consensus_eligible(proposer_node_id, "proposer")
        batch = self.narwhal_store.get_batch(batch_id)
        certificate = self.narwhal_store.get_certificate(batch_id)
        if not certificate or not certificate.available:
            raise ValueError("Batch does not have an available Narwhal certificate")

        view_state = self.hotstuff_store.current_view()
        height = len(self.hotstuff_store.list_commits(limit=10000)) + 1
        block_id = build_block_id(
            view=view_state.view,
            height=height,
            proposer_node_id=proposer_node_id,
            batch_id=batch_id,
            parent_block_id=view_state.last_committed_block_id,
            justify_qc_id=view_state.high_qc_id,
            payload_hash=batch.payload_hash,
        )
        block = HotStuffBlock(
            block_id=block_id,
            view=view_state.view,
            height=height,
            proposer_node_id=proposer_node_id,
            batch_id=batch_id,
            parent_block_id=view_state.last_committed_block_id,
            justify_qc_id=view_state.high_qc_id,
            payload_hash=batch.payload_hash,
        )
        proposal_decision = self._evaluate_fault(
            message_kind=MessageKind.PROPOSAL,
            source_node_id=proposer_node_id,
            target_node_id=None,
            operation_id=None,
            message_id=block.block_id,
            metadata={"batch_id": batch_id, "view": block.view},
        )
        if proposal_decision and (
            proposal_decision.should_drop
            or proposal_decision.blocked_by_partition
            or proposal_decision.leader_failed
        ):
            raise ValueError("HotStuff proposal blocked by fault injection")
        if proposal_decision and proposal_decision.should_equivocate:
            EQUIVOCATION_DETECTOR.record_proposal(
                view=block.view,
                proposer_node_id=proposer_node_id,
                target_node_id=None,
                proposal_id=f"equivocation-marker:{block.block_id[:12]}",
                block_id=f"{block.block_id}:equivocated",
            )
        proposal = self.hotstuff_store.create_proposal(
            block=block,
            batch_certificate_id=certificate.batch_id,
        )
        signed_proposal = self._sign_protocol_message(
            source_node_id=proposer_node_id,
            target_node_id=None,
            message_kind=MessageKind.PROPOSAL,
            operation_id=None,
            correlation_id=proposal.proposal_id,
            body={
                "proposal_id": proposal.proposal_id,
                "block_id": block.block_id,
                "batch_id": batch_id,
                "view": block.view,
            },
        )
        EQUIVOCATION_DETECTOR.record_proposal(
            view=block.view,
            proposer_node_id=proposer_node_id,
            target_node_id=None,
            proposal_id=proposal.proposal_id,
            block_id=block.block_id,
        )
        for operation_id in batch.operation_ids:
            operation = self.operation_store.get(operation_id)
            if operation.status == OperationStatus.AVAILABLE:
                self.operation_store.transition(
                    operation_id=operation_id,
                    to_status=OperationStatus.PROPOSED,
                    protocol=ProtocolName.HOTSTUFF,
                    message="Operation proposed in HotStuff block",
                    node_id=proposer_node_id,
                    details={
                        "proposal_id": proposal.proposal_id,
                        "block_id": block.block_id,
                        "batch_id": batch_id,
                    },
                )

        self._append_event(
            node_id=proposer_node_id,
            operation_id=None,
            status=OperationStatus.PROPOSED,
            message="hotstuff_proposal_created",
            details={
                "proposal_id": proposal.proposal_id,
                "block_id": block.block_id,
                "batch_id": batch_id,
                "view": block.view,
                **(
                    {
                        "signed_message_id": signed_proposal.message_id,
                        "signed_message": signed_proposal.model_dump(mode="json"),
                    }
                    if signed_proposal
                    else {}
                ),
            },
        )
        return proposal

    def vote(
        self,
        proposal_id: str,
        voter_node_id: int,
        accepted: bool = True,
        reason: str | None = None,
        total_nodes: int | None = None,
    ) -> QuorumCertificate | None:
        self._ensure_consensus_eligible(voter_node_id, "voter")
        proposal = self.hotstuff_store.get_proposal(proposal_id)
        message_id = f"{proposal_id}:vote:{voter_node_id}"
        vote_decision = self._evaluate_fault(
            message_kind=MessageKind.VOTE,
            source_node_id=voter_node_id,
            target_node_id=proposal.block.proposer_node_id,
            operation_id=None,
            message_id=message_id,
            metadata={"proposal_id": proposal_id, "block_id": proposal.block.block_id},
        )
        if vote_decision and vote_decision.should_replay:
            if REPLAY_GUARD.check_and_mark(message_id):
                raise ValueError("replay_detected")
        if vote_decision and (vote_decision.should_drop or vote_decision.blocked_by_partition):
            raise ValueError("HotStuff vote blocked by fault injection")
        vote = HotStuffVote(
            vote_id=stable_hash(
                {
                    "proposal_id": proposal_id,
                    "block_id": proposal.block.block_id,
                    "voter_node_id": voter_node_id,
                }
            ),
            proposal_id=proposal_id,
            block_id=proposal.block.block_id,
            voter_node_id=voter_node_id,
            accepted=accepted,
            reason=reason,
            view=proposal.block.view,
        )
        signed_vote = self._sign_protocol_message(
            source_node_id=voter_node_id,
            target_node_id=proposal.block.proposer_node_id,
            message_kind=MessageKind.VOTE,
            operation_id=None,
            correlation_id=proposal_id,
            body={
                "proposal_id": proposal_id,
                "block_id": proposal.block.block_id,
                "voter_node_id": voter_node_id,
                "accepted": accepted,
            },
        )
        qc = self.hotstuff_store.add_vote(
            vote,
            total_nodes=total_nodes or 1,
        )
        self._append_event(
            node_id=voter_node_id,
            operation_id=None,
            status=OperationStatus.VOTED if accepted else OperationStatus.REJECTED,
            message="hotstuff_vote_recorded",
            details={
                "proposal_id": proposal_id,
                "block_id": proposal.block.block_id,
                "accepted": accepted,
                "reason": reason,
                **(
                    {
                        "signed_message_id": signed_vote.message_id,
                        "signed_message": signed_vote.model_dump(mode="json"),
                    }
                    if signed_vote
                    else {}
                ),
            },
        )

        if accepted:
            self._mark_batch_operations(
                proposal.block.batch_id,
                from_status=OperationStatus.PROPOSED,
                to_status=OperationStatus.VOTED,
                message="Operation voted in HotStuff proposal",
                details={"proposal_id": proposal_id, "block_id": proposal.block.block_id},
            )

        if qc:
            self._mark_batch_operations(
                proposal.block.batch_id,
                from_status=OperationStatus.VOTED,
                to_status=OperationStatus.QC_FORMED,
                message="Operation covered by HotStuff quorum certificate",
                details={"proposal_id": proposal_id, "qc_id": qc.qc_id},
            )
            self._append_event(
                node_id=None,
                operation_id=None,
                status=OperationStatus.QC_FORMED,
                message="hotstuff_qc_formed",
                details={
                    "proposal_id": proposal_id,
                    "block_id": qc.block_id,
                    "qc_id": qc.qc_id,
                    "voter_node_ids": qc.voter_node_ids,
                },
            )
        return qc

    def form_qc_demo(
        self,
        proposal_id: str,
        total_nodes: int,
    ) -> QuorumCertificate:
        qc = self.hotstuff_store.get_qc_for_proposal(proposal_id)
        if qc:
            return qc

        for node_id in range(1, total_nodes + 1):
            qc = self.vote(
                proposal_id=proposal_id,
                voter_node_id=node_id,
                accepted=True,
                reason="form-qc-demo vote",
                total_nodes=total_nodes,
            )
            if qc:
                return qc
        raise ValueError("Quorum not reached")

    def commit(self, qc_id: str) -> CommitCertificate:
        qc = self.hotstuff_store.get_qc(qc_id)
        proposal = self.hotstuff_store.get_proposal(qc.proposal_id)
        commit_decision = self._evaluate_fault(
            message_kind=MessageKind.COMMIT,
            source_node_id=proposal.block.proposer_node_id,
            target_node_id=None,
            operation_id=None,
            message_id=qc_id,
            metadata={"proposal_id": proposal.proposal_id, "block_id": proposal.block.block_id},
        )
        if commit_decision and commit_decision.should_replay:
            if REPLAY_GUARD.check_and_mark(qc_id):
                raise ValueError("replay_detected")
        if commit_decision and (
            commit_decision.should_drop or commit_decision.blocked_by_partition
        ):
            raise ValueError("HotStuff commit blocked by fault injection")
        batch = self.narwhal_store.get_batch(proposal.block.batch_id)
        commit = self.hotstuff_store.commit(qc_id, batch.operation_ids)
        self._mark_batch_operations(
            proposal.block.batch_id,
            from_status=OperationStatus.QC_FORMED,
            to_status=OperationStatus.COMMITTED,
            message="Operation committed by HotStuff block",
            details={
                "proposal_id": proposal.proposal_id,
                "block_id": proposal.block.block_id,
                "qc_id": qc_id,
                "commit_id": commit.commit_id,
            },
        )
        self._append_event(
            node_id=None,
            operation_id=None,
            status=OperationStatus.COMMITTED,
            message="hotstuff_block_committed",
            details={
                "proposal_id": proposal.proposal_id,
                "block_id": proposal.block.block_id,
                "qc_id": qc_id,
                "commit_id": commit.commit_id,
                "operation_ids": batch.operation_ids,
            },
        )
        return commit

    def run_hotstuff_demo_for_operation(
        self,
        operation_id: str,
        proposer_node_id: int,
        total_nodes: int,
    ) -> dict:
        batch = self.find_batch_by_operation_id(operation_id)
        if not batch:
            raise KeyError(f"Batch for operation not found: {operation_id}")
        certificate = self.narwhal_store.get_certificate(batch.batch_id)
        if not certificate or not certificate.available:
            raise ValueError("Batch does not have an available Narwhal certificate")

        proposal = self.find_latest_proposal_by_batch_id(batch.batch_id)
        if not proposal:
            proposal = self.create_proposal_from_batch(
                batch_id=batch.batch_id,
                proposer_node_id=proposer_node_id,
                total_nodes=total_nodes,
            )
        qc = self.form_qc_demo(proposal.proposal_id, total_nodes)
        commit = self.commit(qc.qc_id)
        return {
            "proposal": proposal,
            "qc": qc,
            "commit": commit,
        }

    def status(self, limit: int = 100) -> HotStuffStatus:
        return HotStuffStatus(
            view_state=self.hotstuff_store.current_view(),
            proposals=self.hotstuff_store.list_proposals(limit=limit),
            quorum_certificates=self.hotstuff_store.list_qcs(limit=limit),
            committed_blocks=self.hotstuff_store.list_commits(limit=limit),
        )

    def timeout(
        self,
        view: int,
        node_id: int,
        reason: str,
        total_nodes: int,
    ) -> TimeoutCertificate | None:
        certificate = self.hotstuff_store.add_timeout_vote(
            TimeoutVote(node_id=node_id, view=view, reason=reason),
            total_nodes=total_nodes,
        )
        if certificate:
            self._append_event(
                node_id=None,
                operation_id=None,
                status=None,
                message="hotstuff_timeout_certificate_formed",
                details={
                    "tc_id": certificate.tc_id,
                    "view": certificate.view,
                    "voter_node_ids": certificate.voter_node_ids,
                },
            )
        return certificate

    def view_change_demo(
        self,
        total_nodes: int,
        reason: str = "demo_timeout",
    ) -> ViewState:
        current = self.hotstuff_store.current_view()
        for node_id in range(1, total_nodes + 1):
            certificate = self.timeout(current.view, node_id, reason, total_nodes)
            if certificate:
                break
        view_state = self.hotstuff_store.advance_view(total_nodes, reason=reason)
        self._append_event(
            node_id=None,
            operation_id=None,
            status=None,
            message="hotstuff_view_changed",
            details={
                "view": view_state.view,
                "leader_node_id": view_state.leader_node_id,
                "reason": reason,
            },
        )
        return view_state

    def clear(self) -> None:
        self.hotstuff_store.clear()

    def find_batch_by_operation_id(self, operation_id: str):
        for batch in self.narwhal_store.list_batches(limit=10000):
            if operation_id in batch.operation_ids:
                return batch
        return None

    def find_latest_proposal_by_batch_id(
        self,
        batch_id: str,
    ) -> HotStuffProposal | None:
        proposals = [
            proposal
            for proposal in self.hotstuff_store.list_proposals(limit=10000)
            if proposal.block.batch_id == batch_id
        ]
        return proposals[-1] if proposals else None

    def find_qc_by_proposal_id(
        self,
        proposal_id: str,
    ) -> QuorumCertificate | None:
        return self.hotstuff_store.get_qc_for_proposal(proposal_id)

    def find_qc_by_operation_id(
        self,
        operation_id: str,
    ) -> QuorumCertificate | None:
        batch = self.find_batch_by_operation_id(operation_id)
        if not batch:
            return None
        proposal = self.find_latest_proposal_by_batch_id(batch.batch_id)
        if not proposal:
            return None
        return self.find_qc_by_proposal_id(proposal.proposal_id)

    def _mark_batch_operations(
        self,
        batch_id: str,
        *,
        from_status: OperationStatus,
        to_status: OperationStatus,
        message: str,
        details: dict,
    ) -> None:
        batch = self.narwhal_store.get_batch(batch_id)
        for operation_id in batch.operation_ids:
            operation = self.operation_store.get(operation_id)
            if operation.status == from_status:
                self.operation_store.transition(
                    operation_id=operation_id,
                    to_status=to_status,
                    protocol=ProtocolName.HOTSTUFF,
                    message=message,
                    node_id=None,
                    details=details,
                )

    def _ensure_consensus_eligible(self, node_id: int, role: str) -> None:
        if self.swim_store is None:
            return
        try:
            member = self.swim_store.get_member(node_id)
        except KeyError:
            return
        if member.status != NodeStatus.ALIVE:
            raise ValueError(
                f"{role} node {node_id} is not eligible for consensus: {member.status.value}"
            )

    def _evaluate_fault(
        self,
        *,
        message_kind: MessageKind,
        source_node_id: int | None,
        target_node_id: int | None,
        operation_id: str | None,
        message_id: str | None,
        metadata: dict,
    ):
        if self.fault_service is None:
            return None
        return self.fault_service.evaluate(
            FaultEvaluationContext(
                protocol=ProtocolName.HOTSTUFF,
                message_kind=message_kind,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                operation_id=operation_id,
                message_id=message_id,
                metadata=metadata,
            )
        )

    def _sign_protocol_message(
        self,
        *,
        source_node_id: int,
        target_node_id: int | None,
        message_kind: MessageKind,
        operation_id: str | None,
        correlation_id: str | None,
        body: dict,
    ):
        if self.crypto_service is None:
            return None
        payload = BftMessagePayload(
            protocol=ProtocolName.HOTSTUFF,
            message_kind=message_kind,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            operation_id=operation_id,
            correlation_id=correlation_id,
            body=body,
        )
        try:
            return self.crypto_service.sign_message(payload, source_node_id)
        except KeyError:
            self.crypto_service.key_registry.ensure_demo_keys([source_node_id])
            return self.crypto_service.sign_message(payload, source_node_id)

    def _append_event(
        self,
        *,
        node_id: int | None,
        operation_id: str | None,
        status: OperationStatus | None,
        message: str,
        details: dict,
    ) -> None:
        self.event_log.append(
            ProtocolEvent(
                event_id=str(uuid.uuid4()),
                node_id=node_id,
                protocol=ProtocolName.HOTSTUFF,
                operation_id=operation_id,
                status=status,
                message=message,
                details=details,
            )
        )
