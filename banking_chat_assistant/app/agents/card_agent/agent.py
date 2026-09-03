"""Card agent: block/unblock operations. Sensitive actions are idempotency-key protected
at the API layer (see api/v1/cards.py + core/dependencies idempotency handling)."""
from app.agents.tools.banking_tools import CardActionInput, tool_block_card, tool_unblock_card
from app.clients.banking_api_client import BankingAPIClient
from app.schemas.chat import AgentContext, AgentResponse, IntentType


class CardAgent:
    def __init__(self, banking_client: BankingAPIClient) -> None:
        self._banking_client = banking_client

    async def block_card(self, context: AgentContext, card_id: str) -> AgentResponse:
        result = await tool_block_card(
            self._banking_client, CardActionInput(customer_id=context.customer_id, card_id=card_id)
        )
        reply = f"Your {result['card_type'].lower()} card ending {result['card_number_masked'][-4:]} has been blocked."
        return AgentResponse(
            agent_name="card_agent",
            intent=IntentType.CARD_SERVICES,
            reply=reply,
            confidence=1.0,
            tool_calls=["tool_block_card"],
        )

    async def unblock_card(self, context: AgentContext, card_id: str) -> AgentResponse:
        result = await tool_unblock_card(
            self._banking_client, CardActionInput(customer_id=context.customer_id, card_id=card_id)
        )
        reply = f"Your {result['card_type'].lower()} card ending {result['card_number_masked'][-4:]} has been unblocked."
        return AgentResponse(
            agent_name="card_agent",
            intent=IntentType.CARD_SERVICES,
            reply=reply,
            confidence=1.0,
            tool_calls=["tool_unblock_card"],
        )

    async def list_card_status(self, context: AgentContext) -> AgentResponse:
        cards = await self._banking_client.list_cards(context.customer_id)
        if not cards:
            reply = "You don't have any cards on file."
        else:
            lines = [
                f"- {c.card_type.title()} card ending {BankingAPIClient.mask_card_number(c.card_number)[-4:]}: {c.status}"
                for c in cards
            ]
            reply = "Here is your card status:\n" + "\n".join(lines)
        return AgentResponse(
            agent_name="card_agent",
            intent=IntentType.CARD_SERVICES,
            reply=reply,
            confidence=1.0,
            tool_calls=["tool_list_cards"],
        )
