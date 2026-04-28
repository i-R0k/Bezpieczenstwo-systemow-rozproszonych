from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any

from vetclinic_api.bft.common.quorum import quorum_size
from vetclinic_api.bft.hotstuff.models import (
    CommitCertificate,
    HotStuffBlock,
    HotStuffProposal,
    HotStuffVote,
    QuorumCertificate,
    TimeoutCertificate,
    TimeoutVote,
    ViewState,
)


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def leader_for_view(view: int, total_nodes: int) -> int:
    if total_nodes <= 0:
        raise ValueError("total_nodes must be greater than 0")
    return (view % total_nodes) + 1


def build_block_id(
    *,
    view: int,
    height: int,
    proposer_node_id: int,
    batch_id: str,
    parent_block_id: str | None,
    justify_qc_id: str | None,
    payload_hash: str,
) -> str:
    return stable_hash(
        {
            "view": view,
            "height": height,
            "proposer_node_id": proposer_node_id,
            "batch_id": batch_id,
            "parent_block_id": parent_block_id,
            "justify_qc_id": justify_qc_id,
            "payload_hash": payload_hash,
        }
    )


class InMemoryHotStuffStore:
    def __init__(self, total_nodes: int = 1) -> None:
        if total_nodes <= 0:
            raise ValueError("total_nodes must be greater than 0")
        self._view_state = ViewState(
            view=0,
            leader_node_id=leader_for_view(0, total_nodes),
        )
        self._proposals: dict[str, HotStuffProposal] = {}
        self._votes: dict[str, dict[int, HotStuffVote]] = {}
        self._qcs: dict[str, QuorumCertificate] = {}
        self._qcs_by_proposal: dict[str, str] = {}
        self._commits: dict[str, CommitCertificate] = {}
        self._commits_by_block: dict[str, str] = {}
        self._timeout_votes: dict[int, dict[int, TimeoutVote]] = {}
        self._timeout_certificates: dict[int, TimeoutCertificate] = {}
        self._total_nodes = total_nodes
        self._lock = threading.Lock()

    def create_proposal(
        self,
        block: HotStuffBlock,
        batch_certificate_id: str,
    ) -> HotStuffProposal:
        with self._lock:
            proposal_id = stable_hash(
                {
                    "block_id": block.block_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            proposal = HotStuffProposal(
                proposal_id=proposal_id,
                block=block,
                batch_certificate_id=batch_certificate_id,
                created_at=datetime.now(timezone.utc),
            )
            self._proposals[proposal_id] = proposal
            self._votes[proposal_id] = {}
            return proposal

    def get_proposal(self, proposal_id: str) -> HotStuffProposal:
        with self._lock:
            try:
                return self._proposals[proposal_id]
            except KeyError as exc:
                raise KeyError(f"Proposal not found: {proposal_id}") from exc

    def list_proposals(self, limit: int = 100) -> list[HotStuffProposal]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            proposals = list(self._proposals.values())
            if limit == 0:
                return []
            return proposals[-limit:]

    def add_vote(
        self,
        vote: HotStuffVote,
        total_nodes: int,
    ) -> QuorumCertificate | None:
        if total_nodes <= 0:
            raise ValueError("total_nodes must be greater than 0")
        with self._lock:
            if vote.proposal_id not in self._proposals:
                raise KeyError(f"Proposal not found: {vote.proposal_id}")

            proposal_votes = self._votes[vote.proposal_id]
            if vote.voter_node_id not in proposal_votes:
                proposal_votes[vote.voter_node_id] = vote

            if vote.proposal_id in self._qcs_by_proposal:
                return self._qcs[self._qcs_by_proposal[vote.proposal_id]]

            accepted_voters = sorted(
                voter_node_id
                for voter_node_id, stored_vote in proposal_votes.items()
                if stored_vote.accepted
            )
            required = quorum_size(total_nodes)
            if len(accepted_voters) >= required:
                qc_id = stable_hash(
                    {
                        "proposal_id": vote.proposal_id,
                        "block_id": vote.block_id,
                        "view": vote.view,
                        "voter_node_ids": accepted_voters,
                    }
                )
                qc = QuorumCertificate(
                    qc_id=qc_id,
                    proposal_id=vote.proposal_id,
                    block_id=vote.block_id,
                    view=vote.view,
                    voter_node_ids=accepted_voters,
                    quorum_size=required,
                    total_nodes=total_nodes,
                    formed_at=datetime.now(timezone.utc),
                    valid=True,
                )
                self._qcs[qc_id] = qc
                self._qcs_by_proposal[vote.proposal_id] = qc_id
                self._view_state.high_qc_id = qc_id
                self._view_state.locked_qc_id = qc_id
                return qc

            return None

    def get_votes(self, proposal_id: str) -> list[HotStuffVote]:
        with self._lock:
            if proposal_id not in self._proposals:
                raise KeyError(f"Proposal not found: {proposal_id}")
            return list(self._votes.get(proposal_id, {}).values())

    def get_qc(self, qc_id: str) -> QuorumCertificate:
        with self._lock:
            try:
                return self._qcs[qc_id]
            except KeyError as exc:
                raise KeyError(f"QC not found: {qc_id}") from exc

    def get_qc_for_proposal(self, proposal_id: str) -> QuorumCertificate | None:
        with self._lock:
            qc_id = self._qcs_by_proposal.get(proposal_id)
            if not qc_id:
                return None
            return self._qcs[qc_id]

    def list_qcs(self, limit: int = 100) -> list[QuorumCertificate]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            qcs = list(self._qcs.values())
            if limit == 0:
                return []
            return qcs[-limit:]

    def commit(
        self,
        qc_id: str,
        operation_ids: list[str],
    ) -> CommitCertificate:
        with self._lock:
            if qc_id not in self._qcs:
                raise KeyError(f"QC not found: {qc_id}")
            qc = self._qcs[qc_id]
            if qc.block_id in self._commits_by_block:
                raise ValueError(f"Block already committed: {qc.block_id}")
            commit_id = stable_hash(
                {
                    "block_id": qc.block_id,
                    "qc_id": qc_id,
                    "operation_ids": operation_ids,
                }
            )
            commit = CommitCertificate(
                commit_id=commit_id,
                block_id=qc.block_id,
                proposal_id=qc.proposal_id,
                qc_id=qc_id,
                committed_operation_ids=list(operation_ids),
                committed_at=datetime.now(timezone.utc),
            )
            self._commits[commit_id] = commit
            self._commits_by_block[qc.block_id] = commit_id
            self._view_state.last_committed_block_id = qc.block_id
            return commit

    def get_commit(self, commit_id: str) -> CommitCertificate:
        with self._lock:
            try:
                return self._commits[commit_id]
            except KeyError as exc:
                raise KeyError(f"Commit not found: {commit_id}") from exc

    def get_commit_for_block(self, block_id: str) -> CommitCertificate | None:
        with self._lock:
            commit_id = self._commits_by_block.get(block_id)
            if not commit_id:
                return None
            return self._commits[commit_id]

    def list_commits(self, limit: int = 100) -> list[CommitCertificate]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            commits = list(self._commits.values())
            if limit == 0:
                return []
            return commits[-limit:]

    def current_view(self) -> ViewState:
        with self._lock:
            return self._view_state.model_copy()

    def advance_view(
        self,
        total_nodes: int,
        reason: str = "manual_view_change",
    ) -> ViewState:
        del reason
        with self._lock:
            next_view = self._view_state.view + 1
            self._view_state = self._view_state.model_copy(
                update={
                    "view": next_view,
                    "leader_node_id": leader_for_view(next_view, total_nodes),
                }
            )
            self._total_nodes = total_nodes
            return self._view_state.model_copy()

    def add_timeout_vote(
        self,
        timeout_vote: TimeoutVote,
        total_nodes: int,
    ) -> TimeoutCertificate | None:
        if total_nodes <= 0:
            raise ValueError("total_nodes must be greater than 0")
        with self._lock:
            if timeout_vote.view in self._timeout_certificates:
                return self._timeout_certificates[timeout_vote.view]

            votes = self._timeout_votes.setdefault(timeout_vote.view, {})
            if timeout_vote.node_id not in votes:
                votes[timeout_vote.node_id] = timeout_vote

            voter_ids = sorted(votes)
            required = quorum_size(total_nodes)
            if len(voter_ids) >= required:
                tc_id = stable_hash(
                    {
                        "view": timeout_vote.view,
                        "voter_node_ids": voter_ids,
                    }
                )
                certificate = TimeoutCertificate(
                    tc_id=tc_id,
                    view=timeout_vote.view,
                    voter_node_ids=voter_ids,
                    quorum_size=required,
                    total_nodes=total_nodes,
                    formed_at=datetime.now(timezone.utc),
                )
                self._timeout_certificates[timeout_vote.view] = certificate
                return certificate
            return None

    def clear(self) -> None:
        with self._lock:
            leader_node_id = leader_for_view(0, self._total_nodes)
            self._view_state = ViewState(view=0, leader_node_id=leader_node_id)
            self._proposals.clear()
            self._votes.clear()
            self._qcs.clear()
            self._qcs_by_proposal.clear()
            self._commits.clear()
            self._commits_by_block.clear()
            self._timeout_votes.clear()
            self._timeout_certificates.clear()


HOTSTUFF_STORE = InMemoryHotStuffStore()
