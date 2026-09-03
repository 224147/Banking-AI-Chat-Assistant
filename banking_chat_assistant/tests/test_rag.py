import pytest

from app.agents.guardrail_agent.agent import GuardrailAgent
from app.agents.rag_agent.agent import RAGAgent
from app.clients.llm_client import MockLLMClient
from app.schemas.chat import AgentContext, RetrievalContext


class _EmptyRetriever:
    async def retrieve(self, query: str) -> RetrievalContext:
        return RetrievalContext(query=query, documents=[], average_confidence=0.0)


@pytest.mark.asyncio
async def test_rag_agent_returns_fallback_when_no_confident_match():
    agent = RAGAgent(_EmptyRetriever(), MockLLMClient(), GuardrailAgent())
    context = AgentContext(session_id="s1", customer_id="cust_1", request_id="r1", message="random unrelated query")
    response = await agent.answer(context)
    assert response.confidence == 0.0
    assert "couldn't find" in response.reply.lower()
    assert response.citations == []
