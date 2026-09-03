"""LangGraph multi-agent orchestration workflow.

Flow: guardrail (input) -> intent classification -> conditional routing -> domain
agent -> guardrail (output). Built fresh per-request since agents hold request-scoped
dependencies (DB session, clients); the graph shape itself is static.
"""
from langgraph.graph import END, StateGraph

from app.agents.account_agent.agent import AccountAgent
from app.agents.card_agent.agent import CardAgent
from app.agents.guardrail_agent.agent import GuardrailAgent
from app.agents.intent_classifier.classifier import IntentClassifierAgent
from app.agents.loan_agent.agent import LoanAgent
from app.agents.rag_agent.agent import RAGAgent
from app.orchestrator.router import route_by_intent
from app.orchestrator.state import OrchestratorState
from app.schemas.chat import AgentResponse, IntentType


class ChatWorkflow:
    def __init__(
        self,
        guardrail: GuardrailAgent,
        intent_classifier: IntentClassifierAgent,
        account_agent: AccountAgent,
        card_agent: CardAgent,
        loan_agent: LoanAgent,
        rag_agent: RAGAgent,
    ) -> None:
        self._guardrail = guardrail
        self._intent_classifier = intent_classifier
        self._account_agent = account_agent
        self._card_agent = card_agent
        self._loan_agent = loan_agent
        self._rag_agent = rag_agent
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(OrchestratorState)

        graph.add_node("guardrail_input", self._guardrail_input_node)
        graph.add_node("classify_intent", self._classify_intent_node)
        graph.add_node("account_agent", self._account_agent_node)
        graph.add_node("card_agent", self._card_agent_node)
        graph.add_node("loan_agent", self._loan_agent_node)
        graph.add_node("rag_agent", self._rag_agent_node)

        graph.set_entry_point("guardrail_input")
        graph.add_edge("guardrail_input", "classify_intent")
        graph.add_conditional_edges(
            "classify_intent",
            lambda state: route_by_intent(state["intent"]),
            {
                "account_agent": "account_agent",
                "card_agent": "card_agent",
                "loan_agent": "loan_agent",
                "rag_agent": "rag_agent",
            },
        )
        for node in ("account_agent", "card_agent", "loan_agent", "rag_agent"):
            graph.add_edge(node, END)

        return graph.compile()

    async def run(self, context) -> AgentResponse:
        result: OrchestratorState = await self._graph.ainvoke({"context": context})
        return result["response"]

    async def _guardrail_input_node(self, state: OrchestratorState) -> OrchestratorState:
        context = state["context"]
        self._guardrail.screen_input(context.message)
        # LangGraph requires each node to write to at least one state channel.
        return {"context": context}

    async def _classify_intent_node(self, state: OrchestratorState) -> OrchestratorState:
        intent = await self._intent_classifier.classify(state["context"].message)
        return {"intent": intent}

    async def _account_agent_node(self, state: OrchestratorState) -> OrchestratorState:
        context = state["context"]
        if state["intent"] == IntentType.TRANSACTION_HISTORY:
            response = await self._account_agent.handle_transaction_history(context)
        else:
            response = await self._account_agent.handle_balance_inquiry(context)
        return {"response": response}

    async def _card_agent_node(self, state: OrchestratorState) -> OrchestratorState:
        response = await self._card_agent.list_card_status(state["context"])
        return {"response": response}

    async def _loan_agent_node(self, state: OrchestratorState) -> OrchestratorState:
        # Chat flow answers about the customer's primary loan; specific loan_id lookups
        # go through the dedicated /api/v1/loans/details endpoint.
        response = await self._loan_agent.get_primary_loan_details(state["context"])
        return {"response": response}

    async def _rag_agent_node(self, state: OrchestratorState) -> OrchestratorState:
        response = await self._rag_agent.answer(state["context"])
        return {"response": response}
