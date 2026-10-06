"""FastAPI application and same-origin chatbot endpoints."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import Settings, get_settings
from app.models.chat import ChatRequest, ChatResponse
from app.models.feedback import FeedbackRequest
from app.repositories.genie import DatabricksGenieGateway
from app.services.chat_service import ChatService, GenieGateway
from app.telemetry.logging import configure_logging

logger = logging.getLogger(__name__)
_UI_DIRECTORY = Path(__file__).resolve().parents[1] / "ui"


def create_app(settings: Settings | None = None, genie: GenieGateway | None = None) -> FastAPI:
    """Create the HTTP app with injectable settings and Genie gateway."""
    configure_logging()
    configured_settings = settings or get_settings()
    active_genie = genie
    if active_genie is None and configured_settings.genie_configured:
        active_genie = DatabricksGenieGateway(configured_settings)
    chat_service = ChatService(configured_settings, active_genie)

    application = FastAPI(
        title="Unity Catalog Chatbot",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.state.chat_service = chat_service
    application.state.settings = configured_settings

    @application.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(_UI_DIRECTORY / "index.html")

    @application.get("/static/{asset_name}", include_in_schema=False)
    def static_asset(asset_name: str) -> FileResponse:
        if asset_name not in {"chat.js", "styles.css"}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return FileResponse(_UI_DIRECTORY / asset_name)

    @application.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/ready")
    def ready() -> dict[str, str]:
        if not configured_settings.genie_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Genie resource is not configured.",
            )
        return {"status": "ready"}

    @application.get("/api/config")
    def public_config() -> dict[str, int]:
        return {"question_max_chars": configured_settings.question_max_chars}

    @application.post("/api/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        return chat_service.answer(request)

    @application.post("/api/feedback", status_code=status.HTTP_202_ACCEPTED)
    def feedback(request: FeedbackRequest) -> dict[str, str]:
        logger.info(
            "user_feedback correlation_id=%s rating=%s",
            request.correlation_id,
            request.rating,
        )
        return {"status": "accepted"}

    return application


app = create_app()
