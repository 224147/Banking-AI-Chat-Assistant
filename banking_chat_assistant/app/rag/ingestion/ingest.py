"""Seed knowledge-base documents (policies/FAQ) and ingestion entrypoint."""
from app.rag.vectordb.chroma_store import ChromaStore

KNOWLEDGE_BASE_DOCUMENTS = [
    {
        "id": "savings-policy-01",
        "text": (
            "Savings accounts require a minimum balance of $100. Accounts falling below "
            "the minimum balance incur a $5 monthly maintenance fee. Interest is credited "
            "quarterly at an annual rate of 2.5%."
        ),
        "metadata": {"title": "Savings Account Policy", "category": "savings"},
    },
    {
        "id": "credit-card-policy-01",
        "text": (
            "Credit card annual percentage rate (APR) ranges from 18% to 24% based on "
            "credit score. Late payments incur a $35 fee. Cards can be blocked instantly "
            "via the mobile app or chat assistant for lost or stolen cards."
        ),
        "metadata": {"title": "Credit Card Policy", "category": "credit_card"},
    },
    {
        "id": "loan-policy-01",
        "text": (
            "Personal loans are offered at fixed interest rates starting from 9.5% APR "
            "for terms between 12 and 60 months. EMI amounts are calculated using the "
            "reducing balance method. Prepayment is allowed after 6 months without penalty."
        ),
        "metadata": {"title": "Loan Policy", "category": "loan"},
    },
    {
        "id": "faq-01",
        "text": (
            "To reset your online banking password, use the 'Forgot Password' link on the "
            "login page. For balance inquiries, transaction history, or card services, you "
            "can simply ask the chat assistant."
        ),
        "metadata": {"title": "Banking FAQ", "category": "faq"},
    },
    {
        "id": "product-brochure-01",
        "text": (
            "Our premium savings account offers a 3.1% annual interest rate with no "
            "minimum balance requirement for customers enrolled in e-statements."
        ),
        "metadata": {"title": "Product Brochure", "category": "product"},
    },
]


async def ingest_seed_documents(store: ChromaStore) -> None:
    await store.index_documents(KNOWLEDGE_BASE_DOCUMENTS)
