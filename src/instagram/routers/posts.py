"""Post endpoints — POST /posts, GET /posts/{post_id}, media serving."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from instagram.config import settings
from instagram.database import get_db
from instagram.schemas.post import PostResponse
from instagram.services.post_service import (
    FileTooLargeError,
    UserNotFoundError,
    create_post,
    get_post,
)

router = APIRouter(prefix="/posts", tags=["posts"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


def _get_user_id(x_user_id: str | None = Header(None)) -> UUID:
    """Extract and validate X-User-Id header."""
    if not x_user_id:
        raise HTTPException(status_code=422, detail="Missing X-User-Id header")
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid X-User-Id format") from None


@router.post("", status_code=201)
async def create_post_endpoint(
    image: UploadFile | None = File(None),
    caption: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    x_user_id: str | None = Header(None),
):
    """Create a new post with image upload."""
    # Validate user_id header
    if not x_user_id:
        raise HTTPException(status_code=422, detail="Missing X-User-Id header")
    try:
        user_id = UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid X-User-Id format") from None

    # Validate image
    if image is None or image.filename is None:
        raise HTTPException(status_code=422, detail="Image file is required")

    # Validate caption
    if caption is None:
        raise HTTPException(status_code=422, detail="Caption is required")

    # Read image bytes
    image_bytes = await image.read()

    # Check size before processing
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image too large")

    try:
        post = await create_post(
            db,
            user_id=user_id,
            caption=caption,
            image_bytes=image_bytes,
            content_type=image.content_type or "image/jpeg",
        )
        return PostResponse.model_validate(post)
    except FileTooLargeError:
        raise HTTPException(status_code=413, detail="Image too large") from None
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found") from None


@router.get("/{post_id}")
async def get_post_endpoint(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get post by ID."""
    post = await get_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse.model_validate(post)


@router.get("/media/{filename}")
async def serve_media(filename: str):
    """Serve uploaded media files."""
    import os

    path = os.path.join(settings.media_dir, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    # Determine content type from extension
    ext = os.path.splitext(filename)[1].lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")
    return FileResponse(path, media_type=media_type)
