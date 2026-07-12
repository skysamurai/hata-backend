from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.models.parse_task import ParseTask
from app.tasks.parse import parse_region_task

router = APIRouter(prefix="/api/parse", tags=["parser"])


@router.post("/start")
async def start_parse(
    region_id: int,
    source: str = "avito",
    db: AsyncSession = Depends(get_db),
):
    """Start a parse task for a region from a specific source."""
    task = parse_region_task.delay(region_id, source)
    return {"task_id": task.id, "status": "dispatched"}


@router.get("/status/{task_id}")
async def parse_status(task_id: str):
    """Get the status of a Celery task."""
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app
    result = AsyncResult(task_id, app=celery_app)
    response = {"task_id": task_id, "status": result.status}
    if result.ready():
        response["result"] = result.result if result.successful() else str(result.info)
    return response


@router.get("/history")
async def parse_history(
    region_id: int | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get recent parse task history."""
    query = select(ParseTask).order_by(ParseTask.started_at.desc()).limit(limit)
    if region_id:
        query = query.where(ParseTask.region_id == region_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/blacklist")
async def add_to_blacklist(
    phone_hash: str,
    comment: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Add a phone to the blacklist."""
    from app.models.blacklist import Blacklist
    blacklist = Blacklist(phone_hash=phone_hash, comment=comment)
    db.add(blacklist)
    await db.commit()
    return {"status": "added"}
