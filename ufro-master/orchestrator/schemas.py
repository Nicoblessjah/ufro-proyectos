from typing import List, Optional, Literal
from pydantic import BaseModel

DecisionType = Literal["identified", "ambiguous", "unknown"]

class Candidate(BaseModel):
    name: str
    score: float
    threshold: float

class Identity(BaseModel):
    name: str
    score: float

class NormativaAnswer(BaseModel):
    text: str
    citations: list

class IdentifyAndAnswerResponse(BaseModel):
    decision: DecisionType
    identity: Optional[Identity] = None
    candidates: List[Candidate]
    normativa_answer: Optional[NormativaAnswer] = None
    timing_ms: float
    request_id: str
