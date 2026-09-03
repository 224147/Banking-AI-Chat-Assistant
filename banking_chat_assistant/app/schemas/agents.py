"""Card, loan, and complaint request/response schemas."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CardType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class CardStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class CardRequest(BaseModel):
    card_id: str
    card_type: CardType


class CardResponse(BaseModel):
    card_id: str
    card_type: CardType
    status: CardStatus
    card_number_masked: str


class LoanRequest(BaseModel):
    loan_id: str


class LoanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DELINQUENT = "DELINQUENT"


class LoanResponse(BaseModel):
    loan_id: str
    status: LoanStatus
    outstanding_amount: float
    next_emi_amount: float
    next_emi_date: str
    currency: str = "USD"


class ComplaintCategory(str, Enum):
    CARD = "CARD"
    LOAN = "LOAN"
    ACCOUNT = "ACCOUNT"
    SERVICE = "SERVICE"
    OTHER = "OTHER"


class ComplaintStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"


class ComplaintRequest(BaseModel):
    category: ComplaintCategory
    description: str = Field(..., min_length=5, max_length=2000)


class ComplaintResponse(BaseModel):
    complaint_id: str
    category: ComplaintCategory
    status: ComplaintStatus
    description: str
    created_at: datetime
    escalated: bool = False
