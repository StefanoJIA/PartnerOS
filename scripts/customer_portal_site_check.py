"""Validate customer-facing IntelliOpus Portal static site integration.

This check is intentionally read-only. It verifies that the imported customer
portal no longer presents itself as a HOSUN-only Product & Order Portal and that
all customer pages share the IntelliOpus navigation/footer shell.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "frontend" / "public" / "site"
VITE_CONFIG = ROOT / "frontend" / "vite.config.ts"
NGINX_CONFIG = ROOT / "frontend" / "nginx.local-server.conf"
LOCAL_SERVER = ROOT / "scripts" / "customer_portal_local_server.py"

REQUIRED_PAGES = [
    "index.html",
    "about.html",
    "service-history.html",
    "services.html",
    "manufacturers.html",
    "partners.html",
    "products.html",
    "reference-center.html",
    "inventory.html",
    "dashboard.html",
]

PUBLIC_ROUTES = [
    "/",
    "/about",
    "/service-history",
    "/services",
    "/manufacturers",
    "/partners",
    "/login",
    "/change-password",
    "/products",
    "/dashboard",
    "/inventory",
    "/new-order",
    "/reference-center",
    "/customer-service",
    "/order-detail",
    "/product-detail",
    "/user-manual",
    "/product-models",
    "/order-tracking-en",
    "/cart",
    "/order-tracking",
    "/custom-product-request",
    "/order-swatch-set",
    "/product-models-hand-controls",
    "/product-models-accessories",
]


PUBLIC_STORY_PAGES = {"index.html", "about.html", "service-history.html", "services.html", "manufacturers.html", "partners.html"}
THEME_REQUIRED_PAGES = PUBLIC_STORY_PAGES | {
    "cart.html",
    "customer-service.html",
    "custom-product-request.html",
    "dashboard.html",
    "inventory.html",
    "new-order.html",
    "order-detail.html",
    "order-swatch-set.html",
    "product-detail.html",
    "product-models.html",
    "product-models-accessories.html",
    "product-models-hand-controls.html",
    "products.html",
    "reference-center.html",
    "user-manual.html",
}
PORTAL_FLOW_PAGES = {"products.html", "inventory.html", "reference-center.html", "dashboard.html"}
PORTAL_FLOW_LABELS = ["Supplier products", "Local samples", "Approved resources", "Customer workspace"]
AUTH_PAGES = {"login.html", "change-password.html"}
WORKSPACE_PAGES = {
    "cart.html",
    "customer-service.html",
    "custom-product-request.html",
    "dashboard.html",
    "inventory.html",
    "new-order.html",
    "order-detail.html",
    "order-swatch-set.html",
    "order-tracking.html",
    "order-tracking-en.html",
    "product-detail.html",
    "product-models.html",
    "product-models-accessories.html",
    "product-models-hand-controls.html",
    "products.html",
    "reference-center.html",
    "user-manual.html",
}
FORBIDDEN = [
    "Product & Order Portal",
    "Chongqing Huiju",
    "Huiju",
    "JOOBOO",
    "JOOBO",
    "internal PartnerOS execution",
    "PartnerOS execution",
    "partner data is approved",
    "partner products",
    "Catalog by partner",
    "partner program",
    "Internal costs",
    "raw tokens",
    "backend file paths",
    "backend paths",
    "supplier private notes",
    "internal-only operating comments",
    "DOoTYPE",
    "US-ohina",
    "#52657o",
    "costs and margins",
    '<div class="header">',
    '<div class="header portal-header">',
    '<div class="header-content portal-header-inner">',
    '<header class="site-header">',
    '<footer class="footer">',
]

FORBIDDEN_HTML_SNIPPETS = [
    '>Company</a>',
    '<h3>Company</h3>',
    'Track Orders',
    'href="/partners',
    'site-pathway-section',
    'site-pathway-card',
    'workspace-gateway',
    'workspace-gateway-card',
    'JSOe',
    'iseae',
    'mobileeav',
    'resource-hub-grid',
    'workspace-route-strip',
    'site-mode-nav',
    'site-mode-link',
    'workspace-mode-nav',
    'Deeper path',
    'supplier-section',
    'supplier-grid',
    'supplier-card',
    'supplier-badge',
    'supplier-name',
    'supplier-desc',
    'Loading items',
    'Loading tracking information',
    'getOrder status',
    'shippingOrder status',
    'orderOrder status',
]

WORKSPACE_CONTEXT_PAGES = {
    "cart.html",
    "new-order.html",
    "order-detail.html",
    "order-tracking.html",
    "order-tracking-en.html",
    "customer-service.html",
    "custom-product-request.html",
    "product-detail.html",
    "product-models.html",
    "product-models-accessories.html",
    "product-models-hand-controls.html",
    "order-swatch-set.html",
    "user-manual.html",
}
WORKSPACE_FLOW_PAGES = {"cart.html", "new-order.html", "order-detail.html", "customer-service.html"}
WORKSPACE_FLOW_LABELS = ["Product review", "Selected products", "Create order", "Order progress", "Support"]
PRODUCT_DECISION_PAGES = {
    "product-detail.html",
    "product-models.html",
    "product-models-hand-controls.html",
    "product-models-accessories.html",
    "order-swatch-set.html",
    "user-manual.html",
    "custom-product-request.html",
}
PRODUCT_DECISION_LABELS = ["Supplier program", "Product options", "Samples & resources", "Selected products", "Order workspace"]
REQUIRED_CONTENT = {
    "order-detail.html": ["Order progress detail", "Production and shipment progress", "Customer-safe order progress", "Customer-safe production and shipment updates", "Product review", "Selected products", "Create order", "Support"],
    "change-password.html": ["Change Password", "Security notice", "Current password", "New password", "Confirm new password", "Customer Workspace", "auth-footer"],
    "index.html": ["Connect. Source. Deliver.", "bridge-flow-section", "Market side", "IntelliOpus role", "Manufacturer side", 'id="site-reading-path"', "How to use this site", "Understand IntelliOpus", "See the service history", "Review the operating loop", "Compare supplier programs", "Browse product programs", "Continue after sign-in", "JOBO education furniture is active"],
    "about.html": ["Company overview", "Service history", "id=\"operating-history\"", "id=\"operating-bridge\"", "id=\"customer-workspace-path\"", "id=\"operating-principles\"", "Supplier-neutral entry", "Customer-safe workspace", "public-page-summary", "Position", "Scope", "Customer Workspace", "HOSUN", "JOBO", "page-transition-strip", "Company role", "next-step-panel", "Supplier network", "Product programs", "Resources", "Local samples"],
    "service-history.html": ["Service history", "id=\"service-history-overview\"", "id=\"history-timeline\"", "id=\"history-lessons\"", "id=\"history-workspace-path\"", "HOSUN product path", "JOBO education furniture", "Supplier-neutral IntelliOpus", "page-transition-strip", "Real quote and order work", "next-step-panel", "Supplier network", "Product programs", "Resources", "Customer workspace"],
    "services.html": ["Quote support", "Approved customer visibility", "From first review to customer workspace", "id=\"operating-loop\"", "Demand intake", "Supplier fit", "Quote and sample decision", "id=\"connected-workflow\"", "id=\"safety-boundary\"", "id=\"service-workspace-path\"", "public-page-summary", "Discover", "Coordinate", "Improve", "Supplier expansion", "page-transition-strip", "Service model", "next-step-panel", "Product programs", "Resources", "Local samples"],
    "manufacturers.html": ["HOSUN lifting systems", "JOBO education furniture", "Future supplier programs", "supplier-future-card", "customer-safe fields", "Qualified suppliers, connected through one IntelliOpus path", "Peer suppliers", "Separate product rules", "One customer path", "Current supplier programs", "Different product models", "id=\"supplier-workspace-path\"", "id=\"supplier-program-map\"", "How the network works", "Internal side", "From supplier program to customer workspace", "Resources", "Local samples"],
    "partners.html": ["HOSUN lifting systems", "JOBO education furniture", "Future supplier programs", "supplier-future-card", "customer-safe fields", "Qualified suppliers, connected through one IntelliOpus path", "Peer suppliers", "Separate product rules", "One customer path", "Current supplier programs", "Different product models", "id=\"supplier-workspace-path\"", "id=\"supplier-program-map\"", "How the network works", "Internal side", "From supplier program to customer workspace", "Resources", "Local samples"],
    "products.html": ["Product Programs", "portal-showcase-hero", 'id="hosun"', 'id="jobo"', "Supplier programs for product selection", "Approved supplier programs", "catalog-page-summary", "Supplier profile", "Product family", "Customer workspace", "portal-flow-intro", "Customer path", "Sign in to view selectable model families", "partner-program-section", 'id="supplier-programs"', "functional-focus-strip", "Product review", "Choose the supplier program first", "Local samples"],
    "reference-center.html": ["Resources", "portal-showcase-hero", "Approved resources for product decisions", "Official RAL website", "Download RAL guide", "Color confirmation", "Supplier resources", "Order support", "HOSUN lifting systems", "JOBO education furniture", "brand-resource-section", 'id="ral"', 'id="hosun-resources"', 'id="jobo-resources"', "resource-program-map", "Universal color references", "Future supplier resources", "future-resources", "functional-focus-strip", "Resource review", "Use approved files"],
    "inventory.html": ["Local samples", "Sample workflow", "JOBO", "Future suppliers", "workspace-context-band", "workspace-page-summary", "Supplier-separated stock", "functional-focus-strip", "Sample review", "Check local samples", "Product programs", "Resources"],
    "dashboard.html": ["Customer order workspace", "Customer Workspace", "workspace-context-band", "workspace-page-summary", "Product and sample path", "Customer workspace", "portal-flow-intro", "Workspace path", 'id="workspace-journey"', "Workspace scope", "Orders, samples, resources, and support stay together", "functional-focus-strip", "Workspace use", "Continue after product review", "Resources", "Local samples"],
    "order-tracking.html": ["Order status now lives inside the customer workspace", "Workspace compatibility path", "One order area", "Customer-safe view", "Supplier coordination stays internal"],
    "order-tracking-en.html": ["Order status now lives inside the customer workspace", "Workspace compatibility path", "One order area", "Customer-safe view", "Supplier coordination stays internal"],
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    failures: list[str] = []
    html_files = sorted(path.name for path in SITE_DIR.glob("*.html"))

    for page in REQUIRED_PAGES:
        if page not in html_files:
            failures.append(f"missing required page: {page}")

    for page in html_files:
        text = read(SITE_DIR / page)
        if "IntelliOpus Portal" not in text:
            failures.append(f"{page}: missing IntelliOpus Portal identity")
        if page in PORTAL_FLOW_PAGES:
            if "portal-flow-path" not in text:
                failures.append(f"{page}: missing customer portal flow path")
            for label in PORTAL_FLOW_LABELS:
                if label not in text:
                    failures.append(f"{page}: missing customer journey label: {label}")
        if page in THEME_REQUIRED_PAGES and "/css/customer-theme.css" not in text:
            failures.append(f"{page}: missing shared customer theme stylesheet")
        if "portal-footer" not in text:
            failures.append(f"{page}: missing unified footer")
        if page in WORKSPACE_PAGES and "portal-context-band" not in text:
            failures.append(f"{page}: workspace page missing portal context band")
        if page in PUBLIC_STORY_PAGES and page not in {"index.html"} and "company-hero" not in text:
            failures.append(f"{page}: public story page missing company hero")
        if page in PUBLIC_STORY_PAGES and page not in {"index.html"} and "<style" in text:
            failures.append(f"{page}: public story page should use shared theme CSS, not inline styles")
        if page in AUTH_PAGES and "auth-site-strip" not in text:
            failures.append(f"{page}: auth page missing public site navigation strip")
        if page not in AUTH_PAGES and "portal-header" not in text:
            failures.append(f"{page}: missing unified portal header")
        if page in WORKSPACE_CONTEXT_PAGES and "workspace-context-band" not in text:
            failures.append(f"{page}: missing workspace context band")
        if page in WORKSPACE_FLOW_PAGES:
            if "workspace-path-mini" not in text:
                failures.append(f"{page}: missing compact customer workspace path")
            for label in WORKSPACE_FLOW_LABELS:
                if label not in text:
                    failures.append(f"{page}: missing workspace path label: {label}")
        if page in PRODUCT_DECISION_PAGES:
            if "product-decision-path" not in text:
                failures.append(f"{page}: missing product decision path")
            for label in PRODUCT_DECISION_LABELS:
                if label not in text:
                    failures.append(f"{page}: missing product decision path label: {label}")
        if page not in AUTH_PAGES and 'href="/products">Product Programs' not in text:
            failures.append(f"{page}: missing product catalog navigation")
        if page not in AUTH_PAGES and "portal-workspace-menu" not in text:
            failures.append(f"{page}: missing workspace menu")
        if "images.unsplash.com" in text:
            for image_part in text.split("<img"):
                if "images.unsplash.com" in image_part and "onerror=" not in image_part.split(">", 1)[0]:
                    failures.append(f"{page}: external image missing local fallback")
        for word in FORBIDDEN:
            if word in text:
                failures.append(f"{page}: forbidden legacy/customer wording found: {word}")
        for snippet in FORBIDDEN_HTML_SNIPPETS:
            if snippet in text:
                failures.append(f"{page}: forbidden legacy/html snippet found: {snippet}")
        for needle in REQUIRED_CONTENT.get(page, []):
            if needle not in text:
                failures.append(f"{page}: missing required content: {needle}")

    vite = read(VITE_CONFIG)
    nginx = read(NGINX_CONFIG)
    local_server = read(LOCAL_SERVER)
    if "'/': '/site/index.html'" not in vite:
        failures.append("vite route missing: /")
    if "'/service-history': '/site/service-history.html'" not in vite:
        failures.append("vite route missing: /service-history")
    if "'/manufacturers': '/site/manufacturers.html'" not in vite:
        failures.append("vite manufacturers route points to the wrong page")
    if "try_files /site/manufacturers.html /site/index.html" not in nginx:
        failures.append("nginx manufacturers route points to the wrong page")
    if "'/partners': '/site/manufacturers.html'" not in vite:
        failures.append("vite partners route should be a compatibility alias for manufacturers")
    if '"/manufacturers": "site/manufacturers.html"' not in local_server:
        failures.append("local server manufacturers route points to the wrong page")
    if '"/partners": "site/manufacturers.html"' not in local_server:
        failures.append("local server partners route should be a compatibility alias for manufacturers")
    for route in PUBLIC_ROUTES:
        if route != "/" and f"'{route}':" not in vite:
            failures.append(f"vite route missing: {route}")
        if route != "/" and route.strip("/") not in nginx:
            failures.append(f"nginx route missing: {route}")

    if failures:
        print("Customer portal site check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Customer portal site check passed: {len(html_files)} pages, {len(PUBLIC_ROUTES)} public routes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())























