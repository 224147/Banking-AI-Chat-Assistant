"""Tool schemas + thin async wrappers around the Banking API client. Tool schemas are
defined through Pydantic models per requirement, enabling structured tool-calling."""
from pydantic import BaseModel

from app.clients.banking_api_client import BankingAPIClient
from app.core.exceptions import ToolExecutionError


class BalanceInquiryInput(BaseModel):
    customer_id: str


class TransactionHistoryInput(BaseModel):
    customer_id: str
    limit: int = 10


class CardActionInput(BaseModel):
    customer_id: str
    card_id: str


class LoanLookupInput(BaseModel):
    customer_id: str
    loan_id: str


async def tool_get_balance(banking_client: BankingAPIClient, args: BalanceInquiryInput) -> dict:
    try:
        return await banking_client.get_balance(args.customer_id)
    except Exception as exc:
        raise ToolExecutionError("Failed to fetch balance", {"reason": str(exc)}) from exc


async def tool_get_transactions(banking_client: BankingAPIClient, args: TransactionHistoryInput) -> dict:
    try:
        return await banking_client.get_transactions(args.customer_id, args.limit)
    except Exception as exc:
        raise ToolExecutionError("Failed to fetch transactions", {"reason": str(exc)}) from exc


async def tool_block_card(banking_client: BankingAPIClient, args: CardActionInput) -> dict:
    try:
        card = await banking_client.set_card_status(args.customer_id, args.card_id, "BLOCKED")
    except Exception as exc:
        raise ToolExecutionError("Failed to block card", {"reason": str(exc)}) from exc
    return {
        "card_id": card.card_id,
        "card_type": card.card_type,
        "status": card.status,
        "card_number_masked": BankingAPIClient.mask_card_number(card.card_number),
    }


async def tool_unblock_card(banking_client: BankingAPIClient, args: CardActionInput) -> dict:
    try:
        card = await banking_client.set_card_status(args.customer_id, args.card_id, "ACTIVE")
    except Exception as exc:
        raise ToolExecutionError("Failed to unblock card", {"reason": str(exc)}) from exc
    return {
        "card_id": card.card_id,
        "card_type": card.card_type,
        "status": card.status,
        "card_number_masked": BankingAPIClient.mask_card_number(card.card_number),
    }


async def tool_get_loan(banking_client: BankingAPIClient, args: LoanLookupInput) -> dict:
    try:
        loan = await banking_client.get_loan(args.customer_id, args.loan_id)
    except Exception as exc:
        raise ToolExecutionError("Failed to fetch loan", {"reason": str(exc)}) from exc
    return {
        "loan_id": loan.loan_id,
        "status": loan.status,
        "outstanding_amount": loan.outstanding_amount,
        "next_emi_amount": loan.next_emi_amount,
        "next_emi_date": loan.next_emi_date,
    }
