from __future__ import annotations

from typing import Any

import aiohttp_jinja2
from aiohttp import web
from textual_serve.server import Server, to_int


class GomokuServer(Server):
    def __init__(
        self,
        command: str,
        host: str = "localhost",
        port: int = 8000,
        title: str | None = None,
        public_url: str | None = None,
        default_font_size: int = 15,
    ):
        super().__init__(
            command=command,
            host=host,
            port=port,
            title=title,
            public_url=public_url,
        )
        self.default_font_size = default_font_size

    @aiohttp_jinja2.template("app_index.html")
    async def handle_index(self, request: web.Request) -> dict[str, Any]:
        router = request.app.router
        font_size = to_int(
            request.query.get("fontsize", str(self.default_font_size)),
            self.default_font_size,
        )

        def get_url(route: str, **args: str) -> str:
            path = router[route].url_for(**args)
            return f"{self.public_url}{path}"

        def get_websocket_url(route: str, **args: str) -> str:
            url = get_url(route, **args)
            if self.public_url.startswith("https"):
                return "wss:" + url.split(":", 1)[1]
            return "ws:" + url.split(":", 1)[1]

        context: dict[str, Any] = {
            "font_size": font_size,
            "app_websocket_url": get_websocket_url("websocket"),
        }
        context["config"] = {
            "static": {
                "url": get_url("static", filename="/").rstrip("/") + "/",
            }
        }
        context["application"] = {
            "name": self.title,
        }
        return context
