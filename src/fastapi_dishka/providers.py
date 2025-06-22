from typing import Callable, Protocol, Type

from dishka import Provider as DishkaProvider
from dishka import Scope, provide
from dishka.dependency_source import CompositeDependencySource

from fastapi_dishka.middleware import Middleware
from fastapi_dishka.router import APIRouter


class MiddlewareClass(Protocol):
    """Protocol for middleware classes that can be instantiated."""

    def __call__(self, app: object, **kwargs: object) -> Middleware: ...


# Temporary storage for routers and middlewares during class creation
_current_class_routers: list[APIRouter] = []
_current_class_middlewares: list[Type[Middleware]] = []

# Track if we're currently inside a Provider class definition
_inside_provider_class: bool = False


def _clear_all_registries() -> None:
    """Clear all registries for testing purposes."""
    _current_class_routers.clear()
    _current_class_middlewares.clear()


def _collect_routers_from_providers(providers: tuple[DishkaProvider, ...]) -> list[APIRouter]:
    """Collect routers from specific provider instances."""
    routers: list[APIRouter] = []

    for provider in providers:
        provider_class = provider.__class__
        if hasattr(provider_class, "_provided_routers"):
            provided_routers: list[APIRouter] = getattr(provider_class, "_provided_routers", [])
            for router in provided_routers:
                if not any(router is r for r in routers):
                    routers.append(router)

    return routers


def _collect_middlewares_from_providers(providers: tuple[DishkaProvider, ...]) -> list[Type[Middleware]]:
    """Collect middlewares from specific provider instances."""
    middlewares: list[Type[Middleware]] = []

    for provider in providers:
        provider_class = provider.__class__
        if hasattr(provider_class, "_provided_middlewares"):
            provided_middlewares: list[Type[Middleware]] = getattr(provider_class, "_provided_middlewares", [])
            for middleware_class in provided_middlewares:
                if not any(middleware_class is m for m in middlewares):
                    middlewares.append(middleware_class)

    return middlewares


def wrap_router(router: APIRouter) -> Callable[[], APIRouter]:
    """Wrap a router to be automatically collected by the app."""

    @staticmethod  # type: ignore[misc]
    def factory() -> APIRouter:
        return router

    return factory


def provide_router(router: APIRouter) -> CompositeDependencySource:
    """
    Register a router with dependency injection support and return a provider source.

    Args:
        router: FastAPI router to register

    Returns:
        CompositeDependencySource for dependency injection

    Raises:
        RuntimeError: If called outside a Provider class definition
    """
    global _inside_provider_class

    if not _inside_provider_class:
        raise RuntimeError(
            "provide_router() can only be called within a Provider class definition. "
            "This prevents router stealing where routers leak into the next Provider class. "
            "Make sure your Provider class uses ProviderMeta as metaclass."
        )

    _current_class_routers.append(router)
    return provide(source=wrap_router(router), scope=Scope.APP, provides=Type[APIRouter])  # type: ignore[misc]


# Type alias for middleware wrapper protocol
class MiddlewareWrapper(Protocol):
    def __call__(self, middleware_class: Type[Middleware]) -> Type[Middleware]: ...


def wrap_middleware(middleware_class: Type[Middleware]) -> Callable[[], Type[Middleware]]:
    """
    Wrapper function for middleware classes to ensure compatibility.

    Args:
        middleware_class: The middleware class to wrap

    Returns:
        A factory function that returns the wrapped middleware class
    """

    @staticmethod  # type: ignore[misc]
    def factory() -> Type[Middleware]:
        return middleware_class

    return factory


def provide_middleware(middleware_class: Type[Middleware]) -> CompositeDependencySource:
    """
    Register a middleware class with dependency injection support and return a provider source.

    Args:
        middleware_class: Middleware class to register

    Returns:
        CompositeDependencySource for dependency injection

    Raises:
        RuntimeError: If called outside a Provider class definition
    """
    global _inside_provider_class

    if not _inside_provider_class:
        raise RuntimeError(
            "provide_middleware() can only be called within a Provider class definition. "
            "This prevents middleware stealing where middlewares leak into the next Provider class. "
            "Make sure your Provider class uses ProviderMeta as metaclass."
        )

    _current_class_middlewares.append(middleware_class)
    return provide(source=wrap_middleware(middleware_class), scope=Scope.APP, provides=Type[Middleware])


class ProviderMeta(type):
    """Metaclass that collects routers and middlewares during Provider class creation."""

    @classmethod
    def __prepare__(cls, name: str, bases: tuple[type, ...]) -> dict[str, object]:  # type: ignore[override]
        """Set up the namespace for class creation and mark that we're creating a provider."""
        global _inside_provider_class

        # Mark that we're now inside a Provider class definition
        _inside_provider_class = True

        return {}

    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, object]) -> type:
        global _current_class_routers, _current_class_middlewares, _inside_provider_class

        # Let the class be created normally first
        new_class = super().__new__(cls, name, bases, namespace)

        # Move accumulated routers and middlewares to this class
        new_class._provided_routers = _current_class_routers.copy()  # type: ignore[attr-defined]
        new_class._provided_middlewares = _current_class_middlewares.copy()  # type: ignore[attr-defined]

        # Clear temporary storage for next class
        _current_class_routers.clear()
        _current_class_middlewares.clear()

        # Mark that we're no longer inside a Provider class definition
        _inside_provider_class = False

        return new_class


class Provider(DishkaProvider, metaclass=ProviderMeta):
    """
    FastAPI-Dishka Provider with automatic router and middleware registration.

    This Provider class automatically has the ProviderMeta metaclass applied,
    so you can use provide_router() and provide_middleware() without needing
    to manually specify the metaclass.

    Example:
        ```python
        from fastapi_dishka import Provider, provide_router

        class MyProvider(Provider):
            scope = Scope.APP
            api_router = provide_router(my_router)
        ```

    Alternative:
        If you prefer to use dishka.Provider directly, you can still do:
        ```python
        from dishka import Provider
        from fastapi_dishka import ProviderMeta, provide_router

        class MyProvider(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            api_router = provide_router(my_router)
        ```
    """

    pass


class RouterCollectorProvider(DishkaProvider):
    """
    Provider that collects routers from provider instances.
    """

    scope = Scope.APP

    def __init__(self, routers: list[APIRouter]) -> None:
        super().__init__()
        self._routers = routers

    def provide_routers(self) -> list[APIRouter]:
        """Provide the list of collected routers."""
        return self._routers

    routers = provide(source=provide_routers, scope=Scope.APP)


class MiddlewareCollectorProvider(DishkaProvider):
    """
    Provider that collects middleware classes from provider instances.
    """

    scope = Scope.APP
    component = "middlewares"

    def __init__(self, middlewares: list[Type[Middleware]]) -> None:
        super().__init__()
        self._middlewares = middlewares

    def provide_middlewares(self) -> list[Type[Middleware]]:
        """Provide the list of collected middleware classes."""
        return self._middlewares

    middlewares = provide(source=provide_middlewares, scope=Scope.APP)
