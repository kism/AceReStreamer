"""IPTV Pool API endpoints."""

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from acere.api.deps import get_current_user
from acere.instances.iptv_proxy import get_iptv_proxy_manager
from acere.services.iptv_proxy.pool.models import IPTVPoolForAPI, IPTVPoolSourceForAPI
from acere.utils.api_models import MessageResponseModel
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/iptv/pool",
    tags=["IPTV Pool"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
def pool() -> IPTVPoolForAPI:
    """Get all IPTV source pool statuses."""
    manager = get_iptv_proxy_manager()
    return manager.pool.get_all_pool_status()


@router.get("/{source_name}")
def pool_by_source(source_name: str) -> IPTVPoolSourceForAPI:
    """Get pool status for a single IPTV source."""
    manager = get_iptv_proxy_manager()
    result = manager.pool.get_pool_status_by_source(source_name)
    if result is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"No pool found for IPTV source '{source_name}'",
        )
    return result


@router.delete("/{source_name}/slug/{slug}")
def delete_entry(source_name: str, slug: str) -> MessageResponseModel:
    """Remove an entry from an IPTV source pool."""
    manager = get_iptv_proxy_manager()
    if not manager.pool.remove_entry(source_name, slug):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Entry '{slug}' not found in IPTV source pool '{source_name}'",
        )
    return MessageResponseModel(message="IPTV pool entry removed successfully")
