from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dishka import Provider, make_async_container, Scope, from_context
from fastapi import APIRouter, FastAPI
from .providers import RouterCollectorProvider


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

        self.app.state.container = container

        # Get the collected routers from the RouterCollectorProvider
        self.routers = await container.get(list[APIRouter])

        for router in self.routers:
            self.app.include_router(router)
