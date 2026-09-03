"""RAG agent: implements the Embedding -> Vector Search -> Reranking -> Context ->
LLM Response flow, with source citations, confidence scoring, and fallback responses."""
import asyncio

from app.agents.guardrail_agent.agent import GuardrailAgent
from app.clients.llm_client import LLMClient
from app.core.exceptions import AgentTimeoutError
from app.rag.retrieval.retriever import Retriever
from app.schemas.chat import AgentContext, AgentResponse, IntentType

_RAG_TIMEOUT_SECONDS = 30

_FALLBACK_REPLY = (
    "I couldn't find a confident answer to that in our banking knowledge base. "
    "Could you rephrase your question, or would you like me to connect you with a specialist?"
)

_SYSTEM_PROMPT = (
    "You are a banking FAQ assistant. Answer using ONLY the provided context. "
    "If the context is insufficient, say you don't know."
)


class RAGAgent:
    def __init__(self, retriever: Retriever, llm_client: LLMClient, guardrail: GuardrailAgent) -> None:
        self._retriever = retriever
        self._llm_client = llm_client
        self._guardrail = guardrail

    async def answer(self, context: AgentContext) -> AgentResponse:
        try:
            retrieval = await asyncio.wait_for(
                self._retriever.retrieve(context.message), timeout=_RAG_TIMEOUT_SECONDS
            )
        except TimeoutError as exc:
            raise AgentTimeoutError("RAG retrieval timed out") from exc

        if not retrieval.documents or retrieval.average_confidence < 0.05:
            return AgentResponse(
                agent_name="rag_agent",
                intent=IntentType.FAQ,
                reply=_FALLBACK_REPLY,
                citations=[],
                confidence=retrieval.average_confidence,
            )

        sanitized_context = "\n\n".join(
            self._guardrail.screen_untrusted_text(doc.snippet) for doc in retrieval.documents
        )
        user_prompt = f"Context:\n{sanitized_context}\n\nQuestion: {context.message}"
        reply = await self._llm_client.complete(_SYSTEM_PROMPT, user_prompt)

        return AgentResponse(
            agent_name="rag_agent",
            intent=IntentType.FAQ,
            reply=reply,
            citations=retrieval.documents,
            confidence=retrieval.average_confidence,
        )
