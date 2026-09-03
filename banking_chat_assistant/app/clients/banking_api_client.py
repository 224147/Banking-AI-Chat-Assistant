"""Simulated Banking API client. In a real deployment this would call external
core-banking REST/SOAP services over httpx.AsyncClient; here it wraps the local
Postgres-backed domain tables to keep the demo self-contained."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.db.models import Account, Card, Loan, Transaction


def _mask(value: str, keep: int = 4) -> str:
    return f"{'*' * (len(value) - keep)}{value[-keep:]}"


class BankingAPIClient:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_account_for_customer(self, customer_id: str) -> Account:
        result = await self._session.execute(select(Account).where(Account.customer_id == customer_id))
        account = result.scalar_one_or_none()
        if account is None:
            raise ResourceNotFoundError("No account found for customer", {"customer_id": customer_id})
        return account

    async def get_balance(self, customer_id: str) -> dict:
        account = await self.get_account_for_customer(customer_id)
        return {
            "account_number_masked": _mask(account.account_number),
            "available_balance": account.balance,
            "currency": account.currency,
        }

    async def get_transactions(self, customer_id: str, limit: int = 10) -> dict:
        account = await self.get_account_for_customer(customer_id)
        result = await self._session.execute(
            select(Transaction)
            .where(Transaction.account_id == account.account_id)
            .order_by(Transaction.date.desc())
            .limit(limit)
        )
        transactions = result.scalars().all()
        return {
            "account_number_masked": _mask(account.account_number),
            "transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "date": t.date.isoformat(),
                    "description": t.description,
                    "amount": t.amount,
                    "currency": account.currency,
                    "type": t.type,
                }
                for t in transactions
            ],
        }

    async def get_card(self, customer_id: str, card_id: str) -> Card:
        result = await self._session.execute(
            select(Card).where(Card.card_id == card_id, Card.customer_id == customer_id)
        )
        card = result.scalar_one_or_none()
        if card is None:
            raise ResourceNotFoundError("Card not found", {"card_id": card_id})
        return card

    async def set_card_status(self, customer_id: str, card_id: str, status: str) -> Card:
        card = await self.get_card(customer_id, card_id)
        card.status = status
        await self._session.commit()
        await self._session.refresh(card)
        return card

    async def list_cards(self, customer_id: str) -> list[Card]:
        result = await self._session.execute(select(Card).where(Card.customer_id == customer_id))
        return list(result.scalars().all())

    async def get_loan(self, customer_id: str, loan_id: str) -> Loan:
        result = await self._session.execute(
            select(Loan).where(Loan.loan_id == loan_id, Loan.customer_id == customer_id)
        )
        loan = result.scalar_one_or_none()
        if loan is None:
            raise ResourceNotFoundError("Loan not found", {"loan_id": loan_id})
        return loan

    async def get_primary_loan(self, customer_id: str) -> Loan | None:
        result = await self._session.execute(select(Loan).where(Loan.customer_id == customer_id))
        return result.scalars().first()

    @staticmethod
    def mask_card_number(card_number: str) -> str:
        return _mask(card_number)
