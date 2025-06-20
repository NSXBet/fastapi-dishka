from typing import Any, Callable, Type
from dishka.dependency_source import CompositeDependencySource
from fastapi_dishka.router import APIRouter
from dishka import provide, Scope, Provider


# Global registry to collect routers
_router_registry: list[APIRouter] = []

# Global registry to collect middlewares
_middleware_registry: list[Type[Any]] = []


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


def provide_middleware(middleware_class: Type[Any]) -> (
    CompositeDependencySource
    | Callable[
        [Callable[..., Any]],
        CompositeDependencySource,
    ]
):
    """
    Register a middleware class to be automatically collected by the app.

    This function registers the middleware class in a global registry and creates
    a dependency source that the app can use to collect all middlewares.

    Args:
        middleware_class: The middleware class to register (should inherit from fastapi_dishka.Middleware)
    """
    # Register the middleware class in the global registry
    _middleware_registry.append(middleware_class)

    # Create a factory that provides this specific middleware class
    @staticmethod
    def factory() -> Type[Any]:
        return middleware_class

    return provide(source=factory, scope=Scope.APP, provides=Type[Any])


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


class MiddlewareCollectorProvider(Provider):
    """
    Provider that collects all registered middleware classes into a list.
    """

    scope = Scope.APP
    component = "middlewares"

    def provide_middlewares(self) -> list[Type[Any]]:
        """Provide the list of all registered middleware classes."""
        middlewares = _middleware_registry.copy()

        _middleware_registry.clear()

        return middlewares

    middlewares = provide(source=provide_middlewares, scope=Scope.APP)
