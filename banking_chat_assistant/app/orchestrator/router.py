"""Maps a classified intent to the agent node name that should handle it."""
from app.schemas.chat import IntentType

INTENT_TO_NODE = {
    IntentType.BALANCE_INQUIRY: "account_agent",
    IntentType.TRANSACTION_HISTORY: "account_agent",
    IntentType.CARD_SERVICES: "card_agent",
    IntentType.LOAN_INFORMATION: "loan_agent",
    IntentType.FAQ: "rag_agent",
    IntentType.COMPLAINT: "rag_agent",
    IntentType.OTHER: "rag_agent",
}


def route_by_intent(intent: IntentType) -> str:
    return INTENT_TO_NODE.get(intent, "rag_agent")
