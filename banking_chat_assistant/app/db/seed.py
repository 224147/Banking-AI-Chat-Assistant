"""Seed a demo customer with account/card/loan data for local development & tests."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Account, Card, Loan, Transaction

DEMO_CUSTOMER_ID = "cust_demo_001"


async def seed_demo_data(session: AsyncSession) -> None:
    existing = await session.execute(select(Account).where(Account.customer_id == DEMO_CUSTOMER_ID))
    if existing.scalar_one_or_none():
        return

    account = Account(
        customer_id=DEMO_CUSTOMER_ID,
        account_number="1234567890123456",
        balance=5250.75,
        currency="USD",
    )
    session.add(account)
    await session.flush()

    session.add_all(
        [
            Transaction(account_id=account.account_id, description="Grocery Store", amount=-84.20, type="DEBIT"),
            Transaction(account_id=account.account_id, description="Salary Credit", amount=3200.00, type="CREDIT"),
            Transaction(account_id=account.account_id, description="Electric Bill", amount=-120.55, type="DEBIT"),
        ]
    )
    session.add(
        Card(
            customer_id=DEMO_CUSTOMER_ID,
            card_number="4111111111111111",
            card_type="DEBIT",
            status="ACTIVE",
        )
    )
    session.add(
        Card(
            customer_id=DEMO_CUSTOMER_ID,
            card_number="5500000000000004",
            card_type="CREDIT",
            status="ACTIVE",
        )
    )
    session.add(
        Loan(
            customer_id=DEMO_CUSTOMER_ID,
            status="ACTIVE",
            outstanding_amount=12500.00,
            next_emi_amount=450.00,
            next_emi_date="2026-10-05",
        )
    )
    await session.commit()
