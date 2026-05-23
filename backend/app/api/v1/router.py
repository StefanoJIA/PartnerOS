"""Aggregate /api/v1 routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import portal, system

v1_router = APIRouter()
v1_router.include_router(system.router)
v1_router.include_router(portal.router)
