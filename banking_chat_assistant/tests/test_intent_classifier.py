import pytest

from app.agents.intent_classifier.classifier import IntentClassifierAgent
from app.clients.llm_client import MockLLMClient
from app.schemas.chat import IntentType


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message,expected_intent",
    [
        ("What is my account balance?", IntentType.BALANCE_INQUIRY),
        ("Show my recent transactions", IntentType.TRANSACTION_HISTORY),
        ("I need to block my credit card", IntentType.CARD_SERVICES),
        ("What is my loan EMI amount?", IntentType.LOAN_INFORMATION),
        ("I want to raise a complaint about a fraud charge", IntentType.COMPLAINT),
        ("What is the savings account interest rate policy?", IntentType.FAQ),
        # Policy phrasing must win over the generic "balance" noun.
        ("What is the minimum balance policy for savings accounts?", IntentType.FAQ),
        ("Tell me a joke", IntentType.OTHER),
    ],
)
async def test_intent_classifier_fallback_heuristics(message, expected_intent):
    classifier = IntentClassifierAgent(MockLLMClient())
    intent = await classifier.classify(message)
    assert intent == expected_intent
