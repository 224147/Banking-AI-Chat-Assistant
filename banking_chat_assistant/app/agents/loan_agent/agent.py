"""Loan agent: outstanding amount, EMI schedule, loan status lookup."""
from app.agents.tools.banking_tools import LoanLookupInput, tool_get_loan
from app.clients.banking_api_client import BankingAPIClient
from app.schemas.chat import AgentContext, AgentResponse, IntentType


class LoanAgent:
    def __init__(self, banking_client: BankingAPIClient) -> None:
        self._banking_client = banking_client

    async def get_loan_details(self, context: AgentContext, loan_id: str) -> AgentResponse:
        result = await tool_get_loan(
            self._banking_client, LoanLookupInput(customer_id=context.customer_id, loan_id=loan_id)
        )
        reply = (
            f"Loan {result['loan_id']} is {result['status']}. Outstanding amount is "
            f"{result['outstanding_amount']:.2f}. Next EMI of {result['next_emi_amount']:.2f} "
            f"is due on {result['next_emi_date']}."
        )
        return AgentResponse(
            agent_name="loan_agent",
            intent=IntentType.LOAN_INFORMATION,
            reply=reply,
            confidence=1.0,
            tool_calls=["tool_get_loan"],
        )

    async def get_primary_loan_details(self, context: AgentContext) -> AgentResponse:
        loan = await self._banking_client.get_primary_loan(context.customer_id)
        if loan is None:
            return AgentResponse(
                agent_name="loan_agent",
                intent=IntentType.LOAN_INFORMATION,
                reply="You don't have any active loans on file.",
                confidence=1.0,
            )
        return await self.get_loan_details(context, loan.loan_id)
