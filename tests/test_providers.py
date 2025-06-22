"""Tests for fastapi_dishka.providers module."""

import pytest
from dishka import Provider, Scope
from fastapi.testclient import TestClient

from fastapi_dishka import APIRouter, Middleware, provide_middleware, provide_router, start_test, stop_test
from fastapi_dishka.app import App
from fastapi_dishka.providers import (
    MiddlewareCollectorProvider,
    ProviderMeta,
    RouterCollectorProvider,
    _clear_all_registries,
    _collect_middlewares_from_providers,
    _collect_routers_from_providers,
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
        """Clear all registries before each test."""
        _clear_all_registries()

    def test_provide_router_returns_composite_dependency_source(self):
        """Test that provide_router returns a CompositeDependencySource."""
        router = APIRouter(prefix="/test")

        # Create a temporary provider to test provide_router functionality
        class TestProvider(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            test_router = provide_router(router)

        # Verify that the provider was created and has the router
        assert hasattr(TestProvider, "_provided_routers")
        assert len(TestProvider._provided_routers) == 1  # type: ignore[attr-defined]
        assert TestProvider._provided_routers[0] is router  # type: ignore[attr-defined]

    def test_provide_router_outside_provider_class_raises_error(self):
        """Test that provide_router raises RuntimeError when called outside Provider class."""
        router = APIRouter(prefix="/test")

        with pytest.raises(RuntimeError) as exc_info:
            provide_router(router)

        error_message = str(exc_info.value)
        assert "provide_router() can only be called within a Provider class definition" in error_message
        assert "This prevents router stealing" in error_message
        assert "ProviderMeta as metaclass" in error_message

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
        """Clear all registries before each test."""
        _clear_all_registries()

    def test_provide_middleware_returns_composite_dependency_source(self):
        """Test that provide_middleware returns a CompositeDependencySource."""

        # Create a temporary provider to test provide_middleware functionality
        class TestProvider(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            test_middleware = provide_middleware(MiddlewareExample)

        # Verify that the provider was created and has the middleware
        assert hasattr(TestProvider, "_provided_middlewares")
        assert len(TestProvider._provided_middlewares) == 1  # type: ignore[attr-defined]
        assert TestProvider._provided_middlewares[0] is MiddlewareExample  # type: ignore[attr-defined]

    def test_provide_middleware_outside_provider_class_raises_error(self):
        """Test that provide_middleware raises RuntimeError when called outside Provider class."""
        with pytest.raises(RuntimeError) as exc_info:
            provide_middleware(MiddlewareExample)

        error_message = str(exc_info.value)
        assert "provide_middleware() can only be called within a Provider class definition" in error_message
        assert "This prevents middleware stealing" in error_message
        assert "ProviderMeta as metaclass" in error_message

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

    def test_provide_routers_returns_provided_routers(self):
        """Test that provide_routers returns the routers provided to the constructor."""
        router1 = APIRouter(prefix="/test1")
        router2 = APIRouter(prefix="/test2")

        provider = RouterCollectorProvider([router1, router2])
        routers = provider.provide_routers()

        # Should return the provided routers
        assert len(routers) == 2
        assert router1 in routers
        assert router2 in routers

    def test_provide_routers_with_empty_list(self):
        """Test that provide_routers returns empty list when given empty list."""
        provider = RouterCollectorProvider([])
        routers = provider.provide_routers()

        assert routers == []

    def test_provider_has_correct_scope(self):
        """Test that RouterCollectorProvider has APP scope."""
        provider = RouterCollectorProvider([])
        assert provider.scope == Scope.APP


class TestMiddlewareCollectorProvider:
    """Test the MiddlewareCollectorProvider."""

    def test_provide_middlewares_returns_provided_middlewares(self):
        """Test that provide_middlewares returns the middlewares provided to the constructor."""

        class TestMiddleware1(Middleware):
            pass

        class TestMiddleware2(Middleware):
            pass

        provider = MiddlewareCollectorProvider([TestMiddleware1, TestMiddleware2])
        middlewares = provider.provide_middlewares()

        # Should return the provided middlewares
        assert len(middlewares) == 2
        assert TestMiddleware1 in middlewares
        assert TestMiddleware2 in middlewares

    def test_provide_middlewares_with_empty_list(self):
        """Test that provide_middlewares returns empty list when given empty list."""
        provider = MiddlewareCollectorProvider([])
        middlewares = provider.provide_middlewares()

        assert middlewares == []

    def test_provider_has_correct_scope_and_component(self):
        """Test that MiddlewareCollectorProvider has APP scope and middlewares component."""
        provider = MiddlewareCollectorProvider([])
        assert provider.scope == Scope.APP
        assert provider.component == "middlewares"


class TestCollectorFunctions:
    """Test the router and middleware collection functions."""

    def setup_method(self):
        """Clear all registries before each test."""
        _clear_all_registries()

    def test_collect_routers_from_providers_with_metaclass(self):
        """Test that _collect_routers_from_providers extracts routers from provider classes."""
        router1 = APIRouter(prefix="/test1")
        router2 = APIRouter(prefix="/test2")

        class ProviderA(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            router_a = provide_router(router1)

        class ProviderB(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            router_b = provide_router(router2)

        providers = (ProviderA(), ProviderB())
        routers = _collect_routers_from_providers(providers)

        assert len(routers) == 2
        assert router1 in routers
        assert router2 in routers

    def test_collect_middlewares_from_providers_with_metaclass(self):
        """Test that _collect_middlewares_from_providers extracts middlewares from provider classes."""

        class TestMiddleware1(Middleware):
            pass

        class TestMiddleware2(Middleware):
            pass

        class ProviderA(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            middleware_a = provide_middleware(TestMiddleware1)

        class ProviderB(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            middleware_b = provide_middleware(TestMiddleware2)

        providers = (ProviderA(), ProviderB())
        middlewares = _collect_middlewares_from_providers(providers)

        assert len(middlewares) == 2
        assert TestMiddleware1 in middlewares
        assert TestMiddleware2 in middlewares


@pytest.mark.asyncio
async def test_provider_isolation_only_injected_providers_register_routers():
    """Test that only routers from actually injected providers get registered."""
    # Clear registries to ensure clean state
    _clear_all_registries()

    # Create two separate routers
    router_a = APIRouter(prefix="/api-a")
    router_b = APIRouter(prefix="/api-b")

    @router_a.get("/route-1")
    async def route_1():
        return {"route": "1", "provider": "A"}

    @router_b.get("/route-2")
    async def route_2():
        return {"route": "2", "provider": "B"}

    # Create two separate providers
    class ProviderA(Provider, metaclass=ProviderMeta):
        scope = Scope.APP
        api_router_a = provide_router(router_a)

    class ProviderB(Provider, metaclass=ProviderMeta):
        scope = Scope.APP
        api_router_b = provide_router(router_b)

    # Test 1: App with only ProviderA should have route-1 but not route-2
    app_a = App("Test A", "1.0.0", ProviderA())

    try:
        await start_test(app_a, port=9991)
        client_a = TestClient(app_a.app)

        # Should have route-1 from ProviderA
        response_1 = client_a.get("/api-a/route-1")
        assert response_1.status_code == 200
        data_1 = response_1.json()
        assert data_1["route"] == "1"
        assert data_1["provider"] == "A"

        # Should NOT have route-2 from ProviderB (404)
        response_2 = client_a.get("/api-b/route-2")
        assert response_2.status_code == 404

    finally:
        await stop_test(app_a)

    # Test 2: App with only ProviderB should have route-2 but not route-1
    app_b = App("Test B", "1.0.0", ProviderB())

    try:
        await start_test(app_b, port=9992)
        client_b = TestClient(app_b.app)

        # Should have route-2 from ProviderB
        response_2 = client_b.get("/api-b/route-2")
        assert response_2.status_code == 200
        data_2 = response_2.json()
        assert data_2["route"] == "2"
        assert data_2["provider"] == "B"

        # Should NOT have route-1 from ProviderA (404)
        response_1 = client_b.get("/api-a/route-1")
        assert response_1.status_code == 404

    finally:
        await stop_test(app_b)

    # Test 3: App with both providers should have both routes
    app_both = App("Test Both", "1.0.0", ProviderA(), ProviderB())

    try:
        await start_test(app_both, port=9993)
        client_both = TestClient(app_both.app)

        # Should have both routes
        response_1 = client_both.get("/api-a/route-1")
        assert response_1.status_code == 200
        data_1 = response_1.json()
        assert data_1["route"] == "1"
        assert data_1["provider"] == "A"

        response_2 = client_both.get("/api-b/route-2")
        assert response_2.status_code == 200
        data_2 = response_2.json()
        assert data_2["route"] == "2"
        assert data_2["provider"] == "B"

    finally:
        await stop_test(app_both)


class TestSecurityEnforcement:
    """Test that security enforcement prevents provide function misuse."""

    def setup_method(self):
        """Clear all registries before each test."""
        _clear_all_registries()

    def test_provide_functions_work_inside_provider_classes(self):
        """Test that provide functions work correctly when called inside Provider classes."""
        router = APIRouter(prefix="/secure")

        class TestMiddleware(Middleware):
            async def dispatch(self, request, call_next):
                return await call_next(request)

        # This should work without any errors
        class SecureProvider(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            secure_router = provide_router(router)
            secure_middleware = provide_middleware(TestMiddleware)

        # Verify both router and middleware were registered
        assert len(SecureProvider._provided_routers) == 1  # type: ignore[attr-defined]
        assert SecureProvider._provided_routers[0] is router  # type: ignore[attr-defined]
        assert len(SecureProvider._provided_middlewares) == 1  # type: ignore[attr-defined]
        assert SecureProvider._provided_middlewares[0] is TestMiddleware  # type: ignore[attr-defined]

    def test_provide_functions_fail_outside_provider_classes(self):
        """Test that provide functions fail when called outside Provider classes."""
        router = APIRouter(prefix="/insecure")

        class TestMiddleware(Middleware):
            async def dispatch(self, request, call_next):
                return await call_next(request)

        # Both should raise RuntimeError when called outside Provider classes
        with pytest.raises(RuntimeError, match="provide_router.*can only be called within a Provider class"):
            provide_router(router)

        with pytest.raises(RuntimeError, match="provide_middleware.*can only be called within a Provider class"):
            provide_middleware(TestMiddleware)

    def test_no_router_stealing_after_failed_outside_calls(self):
        """Test that failed outside calls don't cause router stealing in subsequent providers."""
        router_legitimate = APIRouter(prefix="/legitimate")
        router_attempted_steal = APIRouter(prefix="/steal-attempt")

        # First, create a legitimate provider
        class LegitimateProvider(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            router = provide_router(router_legitimate)

        # Attempt to call provide_router outside (should fail)
        with pytest.raises(RuntimeError):
            provide_router(router_attempted_steal)

        # Create another provider - it should NOT get the attempted steal router
        class VictimProvider(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            # No routers defined

        # Verify no stealing occurred
        assert len(LegitimateProvider._provided_routers) == 1  # type: ignore[attr-defined]
        assert LegitimateProvider._provided_routers[0] is router_legitimate  # type: ignore[attr-defined]
        assert len(VictimProvider._provided_routers) == 0  # type: ignore[attr-defined]
