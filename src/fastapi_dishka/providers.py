from typing import Callable, Type, TypeVar, Protocol
from dishka.dependency_source import CompositeDependencySource
from fastapi_dishka.router import APIRouter
from fastapi_dishka.middleware import Middleware
from dishka import provide, Scope, Provider

# Type variable for middleware classes
MiddlewareT = TypeVar("MiddlewareT", bound=Middleware)


class MiddlewareClass(Protocol):
    """Protocol for middleware classes that can be instantiated."""

    def __call__(self, app: object, **kwargs: object) -> Middleware: ...


# Global registry to collect routers
_router_registry: list[APIRouter] = []

# Global registry to collect middlewares
_middleware_registry: list[Type[Middleware]] = []


def wrap_router(router: APIRouter) -> Callable[[], APIRouter]:
    """Wrap a router to be automatically collected by the app."""

    def factory() -> APIRouter:
        return router

    return factory


def provide_router(router: APIRouter) -> CompositeDependencySource:
    """
    Register a router to be automatically collected by the app.

    This function registers the router in a global registry and creates
    a dependency source that the app can use to collect all routers.
    """
    # Register the router in the global registry
    _router_registry.append(router)

    return provide(source=wrap_router(router), scope=Scope.APP, provides=APIRouter)  # type: ignore[misc]


def wrap_middleware(middleware_class: Type[MiddlewareT]) -> Callable[[], Type[Middleware]]:
    """Wrap a middleware class to be automatically collected by the app."""

    def factory() -> Type[Middleware]:
        return middleware_class

    return factory


def provide_middleware(middleware_class: Type[MiddlewareT]) -> CompositeDependencySource:
    """
    Register a middleware class to be automatically collected by the app.

    This function registers the middleware class in a global registry and creates
    a dependency source that the app can use to collect all middlewares.

    Args:
        middleware_class: The middleware class to register (should inherit from fastapi_dishka.Middleware)
    """
    # Register the middleware class in the global registry
    _middleware_registry.append(middleware_class)

    return provide(source=wrap_middleware(middleware_class), scope=Scope.APP, provides=Type[Middleware])


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

    def provide_middlewares(self) -> list[Type[Middleware]]:
        """Provide the list of all registered middleware classes."""
        middlewares = _middleware_registry.copy()

        _middleware_registry.clear()

        return middlewares

    middlewares = provide(source=provide_middlewares, scope=Scope.APP)
