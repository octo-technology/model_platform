# Philippe Stepniewski
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from starlette.responses import FileResponse

from backend.api.models_routes import (
    get_model_info_db_handler,
    get_platform_config_handler,
    get_project_registry_tracking_uri,
    get_registry_pool,
)
from backend.api.projects_routes import get_project_db_handler
from backend.domain.entities.role import Role
from backend.domain.ports.model_info_db_handler import ModelInfoDbHandler
from backend.domain.ports.platform_config_handler import PlatformConfigHandler
from backend.domain.ports.project_db_handler import ProjectDbHandler
from backend.domain.ports.registry_handler import RegistryHandler
from backend.domain.use_cases.auth_usecases import get_current_user
from backend.domain.use_cases.compliance_report_usecases import generate_platform_compliance_report

router = APIRouter()


@router.get("/download_report")
def download_platform_compliance_report(
    request: Request,
    current_user: dict = Depends(get_current_user),
    project_db_handler: ProjectDbHandler = Depends(get_project_db_handler),
    model_info_db_handler: ModelInfoDbHandler = Depends(get_model_info_db_handler),
    registry_pool: RegistryHandler = Depends(get_registry_pool),
    platform_config_handler: PlatformConfigHandler = Depends(get_platform_config_handler),
) -> FileResponse:
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")

    logger.info("Generating platform compliance report")

    def tracking_uri_builder(proj):
        return get_project_registry_tracking_uri(proj, request)

    pdf_path = generate_platform_compliance_report(
        project_db_handler=project_db_handler,
        model_info_db_handler=model_info_db_handler,
        registry_pool=registry_pool,
        platform_config_handler=platform_config_handler,
        tracking_uri_builder=tracking_uri_builder,
    )
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"platform_compliance_report_{date_str}.pdf")
