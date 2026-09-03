"""Chat service: builds agent context, runs the LangGraph orchestrator workflow,
publishes lifecycle events, and returns a validated ChatResponse."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.account_agent.agent import AccountAgent
from app.agents.card_agent.agent import CardAgent
from app.agents.guardrail_agent.agent import GuardrailAgent
from app.agents.intent_classifier.classifier import IntentClassifierAgent
from app.agents.loan_agent.agent import LoanAgent
from app.agents.rag_agent.agent import RAGAgent
from app.clients.banking_api_client import BankingAPIClient
from app.clients.llm_client import LLMClient
from app.clients.vector_client import VectorClient
from app.core.config import Settings
from app.events.producer import EventProducer
from app.orchestrator.workflow import ChatWorkflow
from app.rag.embeddings.embedder import get_embedder
from app.rag.retrieval.retriever import Retriever
from app.rag.vectordb.chroma_store import ChromaStore
from app.schemas.chat import AgentContext, ChatRequest, ChatResponse
from app.schemas.events import EventType
from app.services.audit_service import AuditService


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        llm_client: LLMClient,
        vector_client: VectorClient,
        settings: Settings,
        producer: EventProducer,
    ) -> None:
        banking_client = BankingAPIClient(session)
        guardrail = GuardrailAgent()
        embedder = get_embedder(settings)
        store = ChromaStore(vector_client, embedder)
        retriever = Retriever(store, settings)

        self._producer = producer
        self._audit_service = AuditService(session, producer)
        self._workflow = ChatWorkflow(
            guardrail=guardrail,
            intent_classifier=IntentClassifierAgent(llm_client),
            account_agent=AccountAgent(banking_client),
            card_agent=CardAgent(banking_client),
            loan_agent=LoanAgent(banking_client),
            rag_agent=RAGAgent(retriever, llm_client, guardrail),
        )

    async def handle_chat(self, customer_id: str, request_id: str, chat_request: ChatRequest) -> ChatResponse:
        context = AgentContext(
            session_id=chat_request.session_id,
            customer_id=customer_id,
            request_id=request_id,
            message=chat_request.message,
        )

        await self._producer.publish(
            EventType.CHAT_MESSAGE_RECEIVED,
            request_id,
            session_id=chat_request.session_id,
            customer_id=customer_id,
        )

        agent_response = await self._workflow.run(context)

        await self._producer.publish(
            EventType.INTENT_CLASSIFIED,
            request_id,
            session_id=chat_request.session_id,
            customer_id=customer_id,
            payload={"intent": agent_response.intent.value},
        )
        await self._producer.publish(
            EventType.AGENT_SELECTED,
            request_id,
            session_id=chat_request.session_id,
            customer_id=customer_id,
            payload={"agent_name": agent_response.agent_name},
        )
        if agent_response.citations:
            await self._producer.publish(
                EventType.RAG_DOCUMENTS_RETRIEVED,
                request_id,
                session_id=chat_request.session_id,
                customer_id=customer_id,
                payload={
                    "document_ids": [c.document_id for c in agent_response.citations],
                    "average_confidence": agent_response.confidence,
                },
            )
        await self._producer.publish(
            EventType.AGENT_EXECUTED,
            request_id,
            session_id=chat_request.session_id,
            customer_id=customer_id,
            payload={"agent_name": agent_response.agent_name, "intent": agent_response.intent.value},
        )
        await self._producer.publish(
            EventType.RESPONSE_GENERATED,
            request_id,
            session_id=chat_request.session_id,
            customer_id=customer_id,
        )

        # Audit trail: persisted for compliance, never contains the raw prompt.
        await self._audit_service.record(
            EventType.RESPONSE_GENERATED,
            request_id,
            session_id=chat_request.session_id,
            customer_id=customer_id,
            payload={"intent": agent_response.intent.value, "agent_name": agent_response.agent_name},
        )

        return ChatResponse(
            session_id=chat_request.session_id,
            intent=agent_response.intent,
            reply=agent_response.reply,
            citations=agent_response.citations,
            confidence=agent_response.confidence,
            agent_name=agent_response.agent_name,
            request_id=request_id,
        )


def new_request_id() -> str:
    return str(uuid.uuid4())
