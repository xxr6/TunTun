"""API v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1 import ai, auth, cards, checkin, decks, documents, extract, files, focus, plans, review, stats

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(decks.router)
api_router.include_router(cards.router)
api_router.include_router(review.router)
api_router.include_router(files.router)
api_router.include_router(documents.router)
api_router.include_router(ai.router)
api_router.include_router(extract.router)
api_router.include_router(focus.router)
api_router.include_router(stats.router)
api_router.include_router(checkin.router)
api_router.include_router(plans.router)

# 后续挂载：qa / jobs / admin
