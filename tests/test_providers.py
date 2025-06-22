"""Tests for fastapi_dishka.providers module."""

from dishka import Scope
from dishka.dependency_source import CompositeDependencySource

from fastapi_dishka import APIRouter, Middleware, provide_middleware, provide_router
from fastapi_dishka.providers import (
    MiddlewareCollectorProvider,
    RouterCollectorProvider,
    _middleware_registry,
    _router_registry,
    wrap_middleware,
    wrap_router,
)


class MiddlewareExample(Middleware):
    """Test middleware for testing."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Test"] = "test"
        return response


class TestProvideRouter:
    """Test the provide_router function."""

    def setup_method(self):
        """Clear registries before each test."""
        _router_registry.clear()
        _middleware_registry.clear()

    def test_provide_router_returns_composite_dependency_source(self):
        """Test that provide_router returns a CompositeDependencySource."""
        router = APIRouter(prefix="/test")

        result = provide_router(router)

        assert isinstance(result, CompositeDependencySource)

    def test_provide_router_registers_router_in_global_registry(self):
        """Test that provide_router adds router to global registry."""
        router = APIRouter(prefix="/test")

        # Registry should be empty initially
        assert len(_router_registry) == 0

        provide_router(router)

        # Router should be registered
        assert len(_router_registry) == 1
        assert _router_registry[0] is router

    def test_wrap_router_returns_factory_function(self):
        """Test that wrap_router returns a function that returns the router."""
        router = APIRouter(prefix="/test")

        factory = wrap_router(router)

        # Factory should be callable
        assert callable(factory)

        # Factory should return the original router
        result = factory()
        assert result is router


class TestProvideMiddleware:
    """Test the provide_middleware function."""

    def setup_method(self):
        """Clear registries before each test."""
        _router_registry.clear()
        _middleware_registry.clear()

    def test_provide_middleware_returns_composite_dependency_source(self):
        """Test that provide_middleware returns a CompositeDependencySource."""
        result = provide_middleware(MiddlewareExample)

        assert isinstance(result, CompositeDependencySource)

    def test_provide_middleware_registers_middleware_in_global_registry(self):
        """Test that provide_middleware adds middleware to global registry."""
        # Registry should be empty initially
        assert len(_middleware_registry) == 0

        provide_middleware(MiddlewareExample)

        # Middleware should be registered
        assert len(_middleware_registry) == 1
        assert _middleware_registry[0] is MiddlewareExample

    def test_wrap_middleware_returns_factory_function(self):
        """Test that wrap_middleware returns a function that returns the middleware class."""
        factory = wrap_middleware(MiddlewareExample)

        # Factory should be callable
        assert callable(factory)

        # Factory should return the original middleware class
        result = factory()
        assert result is MiddlewareExample


class TestRouterCollectorProvider:
    """Test the RouterCollectorProvider."""

    def setup_method(self):
        """Clear registries before each test."""
        _router_registry.clear()
        _middleware_registry.clear()

    def test_provide_routers_returns_copy_of_registry(self):
        """Test that provide_routers returns a copy of registered routers."""
        router1 = APIRouter(prefix="/test1")
        router2 = APIRouter(prefix="/test2")

        # Register routers
        _router_registry.extend([router1, router2])

        provider = RouterCollectorProvider()
        routers = provider.provide_routers()

        # Should return the registered routers
        assert len(routers) == 2
        assert router1 in routers
        assert router2 in routers

    def test_provide_routers_clears_registry_after_collection(self):
        """Test that provide_routers clears the registry after collecting."""
        router = APIRouter(prefix="/test")

        # Register router
        _router_registry.append(router)
        assert len(_router_registry) == 1

        provider = RouterCollectorProvider()
        provider.provide_routers()

        # Registry should be cleared
        assert len(_router_registry) == 0

    def test_provide_routers_with_empty_registry(self):
        """Test that provide_routers returns empty list when registry is empty."""
        provider = RouterCollectorProvider()
        routers = provider.provide_routers()

        assert routers == []

    def test_provider_has_correct_scope(self):
        """Test that RouterCollectorProvider has APP scope."""
        provider = RouterCollectorProvider()
        assert provider.scope == Scope.APP


class TestMiddlewareCollectorProvider:
    """Test the MiddlewareCollectorProvider."""

    def setup_method(self):
        """Clear registries before each test."""
        _router_registry.clear()
        _middleware_registry.clear()

    def test_provide_middlewares_returns_copy_of_registry(self):
        """Test that provide_middlewares returns a copy of registered middlewares."""

        class TestMiddleware1(Middleware):
            pass

        class TestMiddleware2(Middleware):
            pass

        # Register middlewares
        _middleware_registry.extend([TestMiddleware1, TestMiddleware2])

        provider = MiddlewareCollectorProvider()
        middlewares = provider.provide_middlewares()

        # Should return the registered middlewares
        assert len(middlewares) == 2
        assert TestMiddleware1 in middlewares
        assert TestMiddleware2 in middlewares

    def test_provide_middlewares_clears_registry_after_collection(self):
        """Test that provide_middlewares clears the registry after collecting."""
        # Register middleware
        _middleware_registry.append(MiddlewareExample)
        assert len(_middleware_registry) == 1

        provider = MiddlewareCollectorProvider()
        provider.provide_middlewares()

        # Registry should be cleared
        assert len(_middleware_registry) == 0

    def test_provide_middlewares_with_empty_registry(self):
        """Test that provide_middlewares returns empty list when registry is empty."""
        provider = MiddlewareCollectorProvider()
        middlewares = provider.provide_middlewares()

        assert middlewares == []

    def test_provider_has_correct_scope_and_component(self):
        """Test that MiddlewareCollectorProvider has APP scope and middlewares component."""
        provider = MiddlewareCollectorProvider()
        assert provider.scope == Scope.APP
        assert provider.component == "middlewares"


class TestConcurrentAccess:
    """Test that multiple providers don't interfere with each other."""

    def setup_method(self):
        """Clear registries before each test."""
        _router_registry.clear()
        _middleware_registry.clear()

    def test_multiple_router_registrations_dont_interfere(self):
        """Test that multiple router registrations don't interfere."""
        router1 = APIRouter(prefix="/test1")
        router2 = APIRouter(prefix="/test2")

        # Register routers from different "providers"
        provide_router(router1)
        provide_router(router2)

        # Collect them
        provider = RouterCollectorProvider()
        routers = provider.provide_routers()

        assert len(routers) == 2
        assert router1 in routers
        assert router2 in routers

        # Registry should be cleared
        assert len(_router_registry) == 0

    def test_multiple_middleware_registrations_dont_interfere(self):
        """Test that multiple middleware registrations don't interfere."""

        class TestMiddleware1(Middleware):
            pass

        class TestMiddleware2(Middleware):
            pass

        # Register middlewares from different "providers"
        provide_middleware(TestMiddleware1)
        provide_middleware(TestMiddleware2)

        # Collect them
        provider = MiddlewareCollectorProvider()
        middlewares = provider.provide_middlewares()

        assert len(middlewares) == 2
        assert TestMiddleware1 in middlewares
        assert TestMiddleware2 in middlewares

        # Registry should be cleared
        assert len(_middleware_registry) == 0

    def test_router_and_middleware_registries_are_independent(self):
        """Test that router and middleware registries don't affect each other."""
        router = APIRouter(prefix="/test")

        # Register router and middleware
        provide_router(router)
        provide_middleware(MiddlewareExample)

        # Collect only routers
        router_provider = RouterCollectorProvider()
        routers = router_provider.provide_routers()

        # Only router registry should be cleared
        assert len(routers) == 1
        assert routers[0] is router
        assert len(_router_registry) == 0
        assert len(_middleware_registry) == 1  # Middleware still there

        # Now collect middlewares
        middleware_provider = MiddlewareCollectorProvider()
        middlewares = middleware_provider.provide_middlewares()

        # Now middleware registry should be cleared
        assert len(middlewares) == 1
        assert middlewares[0] is MiddlewareExample
        assert len(_middleware_registry) == 0
