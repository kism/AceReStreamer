"""Blueprint for the Frontend Endpoints."""

import json
import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse

from acere.constants import DIST_DIR
from acere.instances.config import settings
from acere.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Frontend"])

GENERATED_FRONTEND_PATHS = Path(__file__).parent / "generated_frontend_paths.json"

# If there is no frontend host, we assume we are the frontend host
# Generally we just use a separate host for dev with vite
if settings.FRONTEND_HOST == "":
    logger.debug("Frontend: Serving from FastAPI.")

    INDEX_HTML = DIST_DIR / "index.html"
    if not INDEX_HTML.exists():
        msg = "The frontend has not been built. Please refer to the documentation."
        msg += " Expected index.html at: " + str(INDEX_HTML.resolve())
        msg += " Files in directory: " + ", ".join([str(p.name) for p in DIST_DIR.iterdir()])
        raise RuntimeError(
            msg,
        )

    INDEX_HTML_CACHE = INDEX_HTML.read_text()
    VITE_ASSETS_PATH = DIST_DIR / "assets"

    ALL_VITE_STATIC: dict[Path, tuple[bytes, str]] = {}
    for path in VITE_ASSETS_PATH.rglob("*.*"):
        if path.is_file():
            mime_type, _ = mimetypes.guess_type(path.name)
            if mime_type is None:
                mime_type = "application/octet-stream"
            ALL_VITE_STATIC[path.relative_to(VITE_ASSETS_PATH)] = (
                path.read_bytes(),
                mime_type,
            )

    all_paths: list[str] = []
    with GENERATED_FRONTEND_PATHS.open(encoding="utf-8") as f:
        all_paths_json = json.load(f)

    if isinstance(all_paths_json, list):
        all_paths = [str(p) for p in all_paths_json if isinstance(p, str)]
    else:
        msg = "The generated_frontend_paths.json file is not in the expected format."
        raise RuntimeError(
            msg,
        )

    @router.get("/", response_class=HTMLResponse, name="frontend_index")
    @router.get("/index.html", response_class=HTMLResponse, name="frontend_index.html")
    def get_frontend_index() -> Response:
        return HTMLResponse(content=INDEX_HTML_CACHE)

    # Register routes dynamically from all_paths
    for found_path in all_paths:
        # Skip /assets/* paths - they should be served by the catch-all route
        if found_path.startswith("/assets/"):
            continue
        router.add_api_route(
            found_path,
            get_frontend_index,
            methods=["GET"],
            response_class=HTMLResponse,
            name=f"frontend_{found_path.replace('/', '_').strip('_')}",
        )

    @router.get(
        "/assets/{full_path:path}",
        name="frontend_catch_all",
    )
    def get_frontend_catch_all(full_path: str) -> Response:
        """Catch all route to serve frontend files."""
        requested_path = DIST_DIR / full_path
        relative_path = requested_path.relative_to(DIST_DIR)

        if relative_path in ALL_VITE_STATIC:
            content, mime_type = ALL_VITE_STATIC[relative_path]
            return Response(content=content, media_type=mime_type)

        raise HTTPException(status_code=404, detail="File not found")


else:
    logger.debug(
        "Frontend: Assuming separate frontend server",
    )

    @router.get("/", response_class=HTMLResponse, name="frontend_index")
    @router.get("/index.html", response_class=HTMLResponse, name="frontend_index.html")
    def get_frontend_index() -> Response:
        raise HTTPException(
            status_code=404,
            detail="The frontend has not been set up. Please refer to the documentation.",
        )
