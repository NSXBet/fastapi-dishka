import asyncio
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dishka.integrations.fastapi import DishkaRoute, setup_dishka
from dishka import Provider, make_async_container, Scope, from_context
from fastapi import FastAPI
import uvicorn
from fastapi_dishka.providers import RouterCollectorProvider
from fastapi_dishka.router import APIRouter


@asynccontextmanager
async def default_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Default lifespan context manager for FastAPI applications.

    Handles container cleanup on application shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None during application lifespan
    """
    yield
    # Clean up dishka container on shutdown
    if hasattr(app.state, "container"):
        await app.state.container.close()


class App:
    def __init__(
        self,
        title: str,
        version: str = "0.1.0",
        *providers: Provider,
        summary: str = "",
        description: str = "",
    ):
        self.app = FastAPI(
            title=title,
            version=version,
            summary=summary,
            description=description,
            lifespan=default_lifespan,
        )

        self.providers = providers
        self.routers: list[APIRouter] = []
        self._server = None
        self._thread = None

    async def _resolve_container(self):
        class AppProvider(Provider):
            scope = Scope.APP
            app = from_context(provides=App)

        # Always include the RouterCollectorProvider to collect routers
        all_providers = (
            AppProvider(),
            RouterCollectorProvider(),
            *self.providers,
        )

        container = make_async_container(
            *all_providers,
            context={
                App: self,
            },
        )

        setup_dishka(container=container, app=self.app)

        self.app.state.container = container

        # Get the collected routers from the RouterCollectorProvider
        self.routers = await container.get(list[APIRouter])

        for router in self.routers:
            self.app.include_router(router)

    def start(self, blocking: bool = True, host: str = "127.0.0.1", port: int = 8000) -> None:
        """
        Start the FastAPI application using uvicorn.

        Args:
            blocking: If True, blocks until the server stops. If False, starts in a separate thread.
            host: Host to bind to
            port: Port to bind to
        """
        if not blocking:
            self._start_non_blocking(host, port)
        else:
            uvicorn.run(self.app, host=host, port=port)

    def _start_non_blocking(self, host: str, port: int) -> None:
        """Start the server in a separate thread."""

        def run_server():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            config = uvicorn.Config(self.app, host=host, port=port)
            self._server = uvicorn.Server(config)
            loop.run_until_complete(self._server.serve())

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the non-blocking server."""
        if self._server:
            self._server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
