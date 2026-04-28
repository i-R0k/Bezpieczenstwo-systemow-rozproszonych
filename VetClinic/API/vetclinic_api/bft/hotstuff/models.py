from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class HotStuffBlock(BaseModel):
    block_id: str
    view: int
    height: int
    proposer_node_id: int
    batch_id: str
    parent_block_id: str | None = None
    justify_qc_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload_hash: str


class HotStuffProposal(BaseModel):
    proposal_id: str
    block: HotStuffBlock
    batch_certificate_id: str
    signature: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HotStuffVote(BaseModel):
    vote_id: str
    proposal_id: str
    block_id: str
    voter_node_id: int
    accepted: bool
    reason: str | None = None
    view: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuorumCertificate(BaseModel):
    qc_id: str
    proposal_id: str
    block_id: str
    view: int
    voter_node_ids: list[int]
    quorum_size: int
    total_nodes: int
    formed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid: bool


class CommitCertificate(BaseModel):
    commit_id: str
    block_id: str
    proposal_id: str
    qc_id: str
    committed_operation_ids: list[str]
    committed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ViewState(BaseModel):
    view: int
    leader_node_id: int
    high_qc_id: str | None = None
    locked_qc_id: str | None = None
    last_committed_block_id: str | None = None


class TimeoutVote(BaseModel):
    node_id: int
    view: int
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TimeoutCertificate(BaseModel):
    tc_id: str
    view: int
    voter_node_ids: list[int]
    quorum_size: int
    total_nodes: int
    formed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HotStuffStatus(BaseModel):
    view_state: ViewState
    proposals: list[HotStuffProposal]
    quorum_certificates: list[QuorumCertificate]
    committed_blocks: list[CommitCertificate]
