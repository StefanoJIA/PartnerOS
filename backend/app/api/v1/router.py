"""Aggregate /api/v1 routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import fx_rates, portal, pricing, products, quotes, system

v1_router = APIRouter()
v1_router.include_router(system.router)
v1_router.include_router(portal.router)
v1_router.include_router(products.router)
v1_router.include_router(fx_rates.router)
v1_router.include_router(pricing.router)
v1_router.include_router(quotes.router)
