"""Development-only session token issuance for the demo UI.

This endpoint exists so the local chat UI can authenticate without manual token
copying. It is disabled unless ENVIRONMENT=development, and must never be enabled
in a real deployment where tokens come from the bank's identity provider.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings
from app.core.dependencies import get_app_settings
from app.core.exceptions import AuthenticationError
from app.core.security import issue_session_token
from app.db.seed import DEMO_CUSTOMER_ID

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class DevTokenResponse(BaseModel):
    access_token: str
    customer_id: str
    token_type: str = "bearer"


@router.post("/dev-token", response_model=DevTokenResponse)
async def issue_dev_token(settings: Settings = Depends(get_app_settings)) -> DevTokenResponse:
    if settings.environment != "development":
        raise AuthenticationError("Development token endpoint is disabled in this environment")
    return DevTokenResponse(
        access_token=issue_session_token(DEMO_CUSTOMER_ID, settings),
        customer_id=DEMO_CUSTOMER_ID,
    )
