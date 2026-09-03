"""Loan endpoints."""
from fastapi import APIRouter, Depends

from app.clients.banking_api_client import BankingAPIClient
from app.core.dependencies import get_banking_api_client, get_current_customer
from app.schemas.agents import LoanRequest, LoanResponse
from app.schemas.customer import AuthenticatedCustomer

router = APIRouter(prefix="/api/v1/loans", tags=["loans"])


@router.post("/details", response_model=LoanResponse)
async def loan_details(
    loan_request: LoanRequest,
    customer: AuthenticatedCustomer = Depends(get_current_customer),
    banking_client: BankingAPIClient = Depends(get_banking_api_client),
) -> LoanResponse:
    loan = await banking_client.get_loan(customer.customer_id, loan_request.loan_id)
    return LoanResponse(
        loan_id=loan.loan_id,
        status=loan.status,
        outstanding_amount=loan.outstanding_amount,
        next_emi_amount=loan.next_emi_amount,
        next_emi_date=loan.next_emi_date,
    )
