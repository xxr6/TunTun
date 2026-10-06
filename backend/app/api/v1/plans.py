"""今日计划接口。"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import not_found
from app.models.plan import PlanTask
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate
from app.services.checkin import today_str

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=list[PlanOut])
async def list_plans(
    day: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    day = day or today_str(user.timezone)
    rows = (
        await db.scalars(
            select(PlanTask)
            .where(PlanTask.user_id == user.id, PlanTask.day == day)
            .order_by(PlanTask.created_at.asc())
        )
    ).all()
    return [PlanOut.model_validate(r) for r in rows]


@router.post("", response_model=PlanOut, status_code=201)
async def create_plan(
    body: PlanCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    day = body.day or today_str(user.timezone)
    p = PlanTask(user_id=user.id, day=day, title=body.title)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return PlanOut.model_validate(p)


@router.patch("/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: uuid.UUID, body: PlanUpdate,
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    p = await db.scalar(select(PlanTask).where(PlanTask.id == plan_id, PlanTask.user_id == user.id))
    if p is None:
        raise not_found("计划不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return PlanOut.model_validate(p)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    p = await db.scalar(select(PlanTask).where(PlanTask.id == plan_id, PlanTask.user_id == user.id))
    if p is None:
        raise not_found("计划不存在")
    await db.delete(p)
    await db.commit()
