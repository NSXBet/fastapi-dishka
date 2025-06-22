import asyncio
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Type

import uvicorn
from dishka import AsyncContainer, Provider, Scope, from_context, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from starlette.datastructures import State

from fastapi_dishka.middleware import Middleware
from fastapi_dishka.providers import MiddlewareCollectorProvider, RouterCollectorProvider
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
    app_state: State = app.state
    if hasattr(app_state, "container"):
        container: AsyncContainer = app_state.container
        assert container is not None
        await container.close()


class App:
    def __init__(
        self,
        title: str,
        version: str = "0.1.0",
        *providers: Provider,
        summary: str = "",
        description: str = "",
    ) -> None:
        self.app = FastAPI(
            title=title,
            version=version,
            summary=summary,
            description=description,
            lifespan=default_lifespan,
        )

        self.providers = providers
        self.routers: list[APIRouter] = []
        self.middlewares: list[Type[Middleware]] = []
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None
        self._container_resolved = False

    async def _resolve_container(self) -> None:
        """Resolve the container and register routers and middlewares."""
        if self._container_resolved:
            return

        # Import here to avoid circular imports
        from fastapi_dishka.providers import _collect_middlewares_from_providers, _collect_routers_from_providers

        # Collect routers and middlewares directly from the provider classes
        collected_routers = _collect_routers_from_providers(self.providers)
        collected_middlewares = _collect_middlewares_from_providers(self.providers)

        class AppProvider(Provider):
            scope = Scope.APP
            app = from_context(provides=App)

        # Create collector providers with the collected routers and middlewares
        router_collector = RouterCollectorProvider(collected_routers)
        middleware_collector = MiddlewareCollectorProvider(collected_middlewares)

        # Always include the collectors to collect routers and middlewares
        all_providers = (
            AppProvider(),
            router_collector,
            middleware_collector,
            *self.providers,
        )

        # Create context with proper typing
        context: dict[type[App], App] = {
            App: self,
        }

        container = make_async_container(
            *all_providers,
            context=context,
        )

        setup_dishka(container=container, app=self.app)

        self.app.state.container = container

        # Get the collected routers and middlewares
        self.routers = await container.get(list[APIRouter])
        self.middlewares = await container.get(list[Type[Middleware]], component="middlewares")

        # Register middlewares first (they need to be added before routes)
        for middleware_class in self.middlewares:
            # Add the middleware class to the FastAPI app
            # Starlette will instantiate it and the middleware can access
            # dependencies through app.state.container
            self.app.add_middleware(middleware_class)

        # Register routers
        for router in self.routers:
            self.app.include_router(router)

        self._container_resolved = True

    async def start(self, blocking: bool = True, host: str = "127.0.0.1", port: int = 8000) -> None:
        """
        Start the FastAPI application using uvicorn.

        This method automatically resolves the container and registers all routers and middlewares.

        Args:
            blocking: If True, blocks until the server stops. If False, starts in a separate thread.
            host: Host to bind to
            port: Port to bind to
        """
        # Ensure container is resolved before starting
        await self._resolve_container()

        if not blocking:
            self._start_non_blocking(host, port)
        else:
            # For blocking mode, we need to use uvicorn server directly to avoid event loop conflicts
            config = uvicorn.Config(self.app, host=host, port=port)
            server = uvicorn.Server(config)
            await server.serve()

    def start_sync(self, blocking: bool = True, host: str = "127.0.0.1", port: int = 8000) -> None:
        """
        Synchronous version of start() for backwards compatibility.

        Args:
            blocking: If True, blocks until the server stops. If False, starts in a separate thread.
            host: Host to bind to
            port: Port to bind to
        """
        # Resolve container in a new event loop if not already resolved
        if not self._container_resolved:
            asyncio.run(self._resolve_container())

        if not blocking:
            self._start_non_blocking(host, port)
        else:
            uvicorn.run(self.app, host=host, port=port)

    def _start_non_blocking(self, host: str, port: int) -> None:
        """Start the server in a separate thread."""

        def run_server() -> None:
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

    async def close(self) -> None:
        """Close the dishka container and cleanup resources."""
        if hasattr(self.app.state, "container"):
            container: AsyncContainer = self.app.state.container
            if container is not None:
                await container.close()
