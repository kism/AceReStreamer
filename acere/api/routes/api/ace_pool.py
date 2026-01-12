"""AcePool API Blueprint."""

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from acere.api.deps import get_current_user
from acere.instances.ace_pool import get_ace_pool
from acere.services.ace_pool.models import (
    AcePoolAllStatsApi,
    AcePoolEntryForAPI,
    AcePoolForApi,
    AcePoolStat,
)
from acere.utils.api_models import MessageResponseModel
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ace-pool",
    tags=["Ace Pool"],
    dependencies=[Depends(get_current_user)],
)

content_id_not_found_tmp_str = "Ace content_id '{content_id}' not found in Ace pool"
pid_not_found_tmp_str = "Ace PID '{pid}' not found in Ace pool"


# region /api/ace-pool
@router.get("/")
def pool() -> AcePoolForApi:
    """API endpoint to get the Ace pool."""
    ace_pool = get_ace_pool()
    return ace_pool.get_instances_api()


@router.get("/content_id/{content_id}")
def get_by_content_id(content_id: str) -> AcePoolEntryForAPI:
    """API endpoint to get the Ace pool."""
    ace_pool = get_ace_pool()
    result = ace_pool.get_instance_by_content_id_api(content_id)
    if result is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=MessageResponseModel(message=content_id_not_found_tmp_str.format(content_id=content_id)),
        )

    return result


@router.delete("/content_id/{content_id}")
async def delete_by_content_id(content_id: str) -> MessageResponseModel:
    """API endpoint to delete an Ace instance from the Ace pool."""
    ace_pool = get_ace_pool()
    instance = ace_pool.get_instance_by_content_id_api(content_id)
    if instance is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=MessageResponseModel(message=content_id_not_found_tmp_str.format(content_id=content_id)),
        )

    await ace_pool.remove_instance_by_content_id(content_id, caller="API")
    return MessageResponseModel(message="Ace ID removed successfully")


@router.get("/pid/{pid}")
def get_by_pid(pid: str) -> AcePoolEntryForAPI:
    """API endpoint to get the Ace pool."""
    ace_pool = get_ace_pool()
    if not pid.isdigit():
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=MessageResponseModel(message=pid_not_found_tmp_str.format(pid=pid)),
        )

    pid_int = int(pid)
    instance = ace_pool.get_instance_by_pid_api(pid_int)
    if instance is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=MessageResponseModel(message=pid_not_found_tmp_str.format(pid=pid)),
        )

    return instance


@router.get("/stats")
async def stats() -> list[AcePoolAllStatsApi]:
    """API endpoint to get Ace pool stats."""
    ace_pool = get_ace_pool()
    return await ace_pool.get_all_stats()


@router.get("/stats/content_id/{content_id}")
async def stats_by_content_id(content_id: str) -> AcePoolStat:
    """API endpoint to get Ace pool stats by Ace content ID."""
    ace_pool = get_ace_pool()
    ace_pool_stat = await ace_pool.get_stats_by_content_id(content_id)

    if ace_pool_stat is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=MessageResponseModel(message=content_id_not_found_tmp_str.format(content_id=content_id)),
        )

    return ace_pool_stat


@router.get("/stats/pid/{pid}")
async def stats_by_pid(pid: str) -> AcePoolStat:
    """API endpoint to get Ace pool stats by PID."""
    ace_pool = get_ace_pool()
    try:
        pid_int = int(pid)
        ace_pool_stat = await ace_pool.get_stats_by_pid(pid_int)

        if ace_pool_stat is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=MessageResponseModel(message=pid_not_found_tmp_str.format(pid=pid)),
            )

    except ValueError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=MessageResponseModel(message=pid_not_found_tmp_str.format(pid=pid)),
        )

    return ace_pool_stat
