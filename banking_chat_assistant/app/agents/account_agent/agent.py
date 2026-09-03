"""Account agent: balance inquiries & transaction history."""
from app.agents.tools.banking_tools import (
    BalanceInquiryInput,
    TransactionHistoryInput,
    tool_get_balance,
    tool_get_transactions,
)
from app.clients.banking_api_client import BankingAPIClient
from app.schemas.chat import AgentContext, AgentResponse, IntentType


class AccountAgent:
    def __init__(self, banking_client: BankingAPIClient) -> None:
        self._banking_client = banking_client

    async def handle_balance_inquiry(self, context: AgentContext) -> AgentResponse:
        result = await tool_get_balance(self._banking_client, BalanceInquiryInput(customer_id=context.customer_id))
        reply = (
            f"Your available balance on account ending {result['account_number_masked'][-4:]} "
            f"is {result['available_balance']:.2f} {result['currency']}."
        )
        return AgentResponse(
            agent_name="account_agent",
            intent=IntentType.BALANCE_INQUIRY,
            reply=reply,
            confidence=1.0,
            tool_calls=["tool_get_balance"],
        )

    async def handle_transaction_history(self, context: AgentContext) -> AgentResponse:
        result = await tool_get_transactions(
            self._banking_client, TransactionHistoryInput(customer_id=context.customer_id, limit=5)
        )
        lines = [
            f"- {t['date'][:10]}: {t['description']} ({t['amount']:+.2f} {t['currency']})"
            for t in result["transactions"]
        ]
        reply = "Here are your recent transactions:\n" + "\n".join(lines) if lines else "No recent transactions found."
        return AgentResponse(
            agent_name="account_agent",
            intent=IntentType.TRANSACTION_HISTORY,
            reply=reply,
            confidence=1.0,
            tool_calls=["tool_get_transactions"],
        )
