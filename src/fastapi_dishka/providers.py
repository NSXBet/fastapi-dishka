from typing import Any, Callable
from dishka.dependency_source import CompositeDependencySource
from fastapi_dishka.router import APIRouter
from dishka import provide, Scope, Provider


# Global registry to collect routers
_router_registry: list[APIRouter] = []


def provide_router(router: APIRouter) -> (
    CompositeDependencySource
    | Callable[
        [Callable[..., Any]],
        CompositeDependencySource,
    ]
):
    """
    Register a router to be automatically collected by the app.

    This function registers the router in a global registry and creates
    a dependency source that the app can use to collect all routers.
    """
    # Register the router in the global registry
    _router_registry.append(router)

    # Create a factory that provides this specific router
    @staticmethod
    def factory() -> APIRouter:
        return router

    return provide(source=factory, scope=Scope.APP, provides=APIRouter)


class RouterCollectorProvider(Provider):
    """
    Provider that collects all registered routers into a list.
    """

    scope = Scope.APP

    def provide_routers(self) -> list[APIRouter]:
        """Provide the list of all registered routers."""
        routers = _router_registry.copy()

        _router_registry.clear()

        return routers

    routers = provide(source=provide_routers, scope=Scope.APP)
