"""Aggregate /api/v1 routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    feedback_tickets,
    fx_rates,
    orders,
    portal,
    portal_customer,
    pricing,
    products,
    quote_delivery,
    quote_order_readiness,
    quote_pdf,
    quotes,
    system,
)

v1_router = APIRouter()
v1_router.include_router(system.router)
v1_router.include_router(portal.router)
v1_router.include_router(portal_customer.router)
v1_router.include_router(feedback_tickets.router)
v1_router.include_router(products.router)
v1_router.include_router(fx_rates.router)
v1_router.include_router(pricing.router)
v1_router.include_router(quote_delivery.router)
v1_router.include_router(quote_order_readiness.router)
v1_router.include_router(orders.router)
v1_router.include_router(quotes.router)
v1_router.include_router(quote_pdf.router)
