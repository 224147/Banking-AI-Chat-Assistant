"""Account endpoints (balance inquiry, transaction history)."""
from fastapi import APIRouter, Depends

from app.clients.banking_api_client import BankingAPIClient
from app.core.dependencies import get_banking_api_client, get_current_customer
from app.schemas.customer import (
    AccountBalanceRequest,
    AccountBalanceResponse,
    AccountTransactionsRequest,
    TransactionHistoryResponse,
)
from app.schemas.customer import AuthenticatedCustomer

router = APIRouter(prefix="/api/v1/account", tags=["account"])


@router.post("/balance", response_model=AccountBalanceResponse)
async def get_balance(
    _request: AccountBalanceRequest,
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    banking_client: BankingAPIClient = Depends(get_banking_api_client),
) -> AccountBalanceResponse:
    result = await banking_client.get_balance(customer.customer_id)
    return AccountBalanceResponse(**result)


@router.post("/transactions", response_model=TransactionHistoryResponse)
async def get_transactions(
    request: AccountTransactionsRequest,
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    banking_client: BankingAPIClient = Depends(get_banking_api_client),
) -> TransactionHistoryResponse:
    result = await banking_client.get_transactions(customer.customer_id, request.limit)
    return TransactionHistoryResponse(**result)
