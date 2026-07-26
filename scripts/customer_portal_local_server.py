"""Serve the customer-facing IntelliOpus portal for local review.

This server is intentionally small: it mirrors the customer-site routes used by
Vite and the local-server nginx config so extensionless URLs work during manual
review without requiring Docker.
"""

from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "public"
BACKEND_BASE_URL = "http://127.0.0.1:8014"

ROUTES = {
    "/": "site/index.html",
    "/about": "site/about.html",
    "/service-history": "site/service-history.html",
    "/services": "site/services.html",
    "/manufacturers": "site/manufacturers.html",
    # Compatibility alias only. The public navigation should use /manufacturers.
    "/partners": "site/manufacturers.html",
    "/login": "site/login.html",
    "/change-password": "site/change-password.html",
    "/products": "site/products.html",
    "/dashboard": "site/dashboard.html",
    "/inventory": "site/inventory.html",
    "/new-order": "site/new-order.html",
    "/reference-center": "site/reference-center.html",
    "/customer-service": "site/customer-service.html",
    "/order-detail": "site/order-detail.html",
    "/product-detail": "site/product-detail.html",
    "/user-manual": "site/user-manual.html",
    "/product-models": "site/product-models.html",
    "/order-tracking-en": "site/order-tracking-en.html",
    "/cart": "site/cart.html",
    "/order-tracking": "site/order-tracking.html",
    "/custom-product-request": "site/custom-product-request.html",
    "/order-swatch-set": "site/order-swatch-set.html",
    "/product-models-hand-controls": "site/product-models-hand-controls.html",
    "/product-models-accessories": "site/product-models-accessories.html",
}

PREFIX_ROUTES = {
    "/product-models/": "site/product-models.html",
    "/product-detail/": "site/product-detail.html",
    "/order-detail/": "site/order-detail.html",
    "/order-tracking/": "site/order-tracking.html",
}


class Handler(SimpleHTTPRequestHandler):
    def _proxy_api(self) -> bool:
        path = urlsplit(self.path)
        if not path.path.startswith("/api/"):
            return False
        body = None
        if self.command in {"POST", "PUT", "PATCH"}:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else None
        target = f"{BACKEND_BASE_URL}{self.path}"
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}
        }
        try:
            request = Request(target, data=body, headers=headers, method=self.command)
            with urlopen(request, timeout=12) as response:
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in {"transfer-encoding", "connection", "content-encoding"}:
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
        except HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() not in {"transfer-encoding", "connection", "content-encoding"}:
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)
        except URLError:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                b'{"detail":"Customer portal backend is unavailable. Please start the PartnerOS backend on http://127.0.0.1:8014."}'
            )
        return True

    def do_GET(self) -> None:
        if self._proxy_api():
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self._proxy_api():
            return
        super().do_POST()

    def do_PUT(self) -> None:
        if self._proxy_api():
            return
        super().do_PUT()

    def do_PATCH(self) -> None:
        if self._proxy_api():
            return
        super().do_PATCH()

    def translate_path(self, path: str) -> str:
        path_only = urlsplit(path).path
        if path_only in ROUTES:
            return str(ROOT / ROUTES[path_only])
        for prefix, target in PREFIX_ROUTES.items():
            if path_only.startswith(prefix):
                return str(ROOT / target)
        return str(ROOT / path_only.lstrip("/"))

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8080), Handler)
    print("Customer portal local server: http://127.0.0.1:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()

