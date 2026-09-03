"""Intent classification agent. Validates LLM JSON output via model_validate_json()
and falls back to keyword heuristics when the LLM output is invalid/unavailable
(e.g. the offline mock provider), per the fallback-response requirement."""
import asyncio
import re

from pydantic import BaseModel, ValidationError

from app.clients.llm_client import LLMClient
from app.core.exceptions import AgentTimeoutError
from app.core.logging import get_logger
from app.schemas.chat import IntentType

logger = get_logger(__name__)

_CLASSIFIER_TIMEOUT_SECONDS = 30

_SYSTEM_PROMPT = (
    "You are a banking intent classifier. Respond ONLY with JSON matching "
    '{"intent": "<one of BALANCE_INQUIRY, TRANSACTION_HISTORY, CARD_SERVICES, '
    'LOAN_INFORMATION, FAQ, COMPLAINT, OTHER>"}.'
)

# Ordered by specificity: policy/informational phrasing is checked before generic
# domain nouns so "savings account minimum balance policy" resolves to FAQ, not
# BALANCE_INQUIRY.
_KEYWORD_MAP: list[tuple[re.Pattern, IntentType]] = [
    (re.compile(r"policy|policies|interest rate|\bfaq\b|brochure|eligibility|terms and conditions", re.IGNORECASE), IntentType.FAQ),
    (re.compile(r"complaint|escalate|dispute|unauthorized|fraud", re.IGNORECASE), IntentType.COMPLAINT),
    (re.compile(r"transaction|statement|history", re.IGNORECASE), IntentType.TRANSACTION_HISTORY),
    (re.compile(r"\bcard\b|block|unblock", re.IGNORECASE), IntentType.CARD_SERVICES),
    (re.compile(r"loan|emi|installment", re.IGNORECASE), IntentType.LOAN_INFORMATION),
    (re.compile(r"\bbalance\b", re.IGNORECASE), IntentType.BALANCE_INQUIRY),
    (re.compile(r"how (do|can) i|what is|what are", re.IGNORECASE), IntentType.FAQ),
]


class IntentClassificationResult(BaseModel):
    intent: IntentType


class IntentClassifierAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def classify(self, message: str) -> IntentType:
        try:
            raw = await asyncio.wait_for(
                self._llm_client.complete(_SYSTEM_PROMPT, message, temperature=0.0),
                timeout=_CLASSIFIER_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise AgentTimeoutError("Intent classifier timed out") from exc

        try:
            result = IntentClassificationResult.model_validate_json(raw)
            return result.intent
        except (ValidationError, ValueError):
            logger.info("intent_classifier_fallback_to_heuristics", raw=raw[:100])
            return self._classify_by_keywords(message)

    @staticmethod
    def _classify_by_keywords(message: str) -> IntentType:
        for pattern, intent in _KEYWORD_MAP:
            if pattern.search(message):
                return intent
        return IntentType.OTHER
