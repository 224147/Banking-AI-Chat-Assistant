"""Customer / session schemas."""
from pydantic import BaseModel, Field


class AuthenticatedCustomer(BaseModel):
    customer_id: str


class CustomerProfile(BaseModel):
    customer_id: str
    full_name: str
    email: str
    phone_masked: str


class AccountBalanceResponse(BaseModel):
    account_number_masked: str
    available_balance: float
    currency: str = "USD"


class TransactionItem(BaseModel):
    transaction_id: str
    date: str
    description: str
    amount: float
    currency: str = "USD"
    type: str


class TransactionHistoryResponse(BaseModel):
    account_number_masked: str
    transactions: list[TransactionItem]


class AccountBalanceRequest(BaseModel):
    account_id: str = Field(..., description="Internal account identifier")


class AccountTransactionsRequest(BaseModel):
    account_id: str
    limit: int = Field(default=10, ge=1, le=100)
