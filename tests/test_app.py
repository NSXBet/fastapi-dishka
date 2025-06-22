import asyncio
import time

import httpx
import pytest
from dishka import FromDishka, Provider, Scope, provide
from fastapi.testclient import TestClient

from fastapi_dishka import APIRouter, App, Middleware, provide_middleware, provide_router, start_test, stop_test, test
from fastapi_dishka.providers import ProviderMeta


class Logger:
    """Simple logger service to test dependency chaining."""

    def __init__(self):
        self.logs = []
        self.created_at = time.time()

    def info(self, message: str):
        log_entry = f"[INFO] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def get_logs(self):
        return self.logs.copy()


class Service:
    def __init__(self, logger: FromDishka[Logger]):
        self.counter = 0
        self.logger = logger
        self.logger.info("Service initialized with logger dependency")

    def increment(self):
        self.counter += 1
        self.logger.info(f"Counter incremented to {self.counter}")

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

    def hello(self) -> str:
        return "Hello from service"


class CounterHeaderMiddleware(Middleware):
    """Test middleware that adds a header with the current counter value."""

    async def dispatch(self, request, call_next):
        # Get the service dependency (which should have logger injected)
        service = await self.get_dependency(request, Service)

        # Process the request
        response = await call_next(request)

        # Add a header with the counter value
        response.headers["X-Counter"] = str(service.counter)
        response.headers["X-Logger-Logs"] = str(len(service.logger.get_logs()))

        return response


router = APIRouter(prefix="/router")
router2 = APIRouter(prefix="/router2")


@router.get("/")
def hello_world(service: FromDishka[Service]):
    service.increment()
    return {"message": "Hello, World!"}


@router2.get("/")
def hello_world2():
    return {"message": "Hello, World! 2"}


class LoggerProvider(Provider, metaclass=ProviderMeta):
    """Provider that supplies a logger instance."""

    scope = Scope.APP

    logger = provide(Logger, scope=Scope.APP)


@pytest.mark.asyncio
async def test_app_can_auto_wire_routers():
    class TestProvider(Provider, metaclass=ProviderMeta):
        hello_router = provide_router(router)
        service = provide(Service, scope=Scope.APP)

    app = App("test app", "0.1.0", LoggerProvider(), TestProvider())

    await app._resolve_container()

    assert app.routers is not None
    assert len(app.routers) == 1


@pytest.mark.asyncio
async def test_another_app_can_auto_wire_routers():
    class AnotherTestProvider(Provider, metaclass=ProviderMeta):
        hello_router = provide_router(router)
        service = provide(Service, scope=Scope.APP)

    app = App("test app", "0.1.0", LoggerProvider(), AnotherTestProvider())

    await app._resolve_container()

    assert app.routers is not None
    assert len(app.routers) == 1


@pytest.mark.asyncio
async def test_another_app_can_auto_wire_more_than_one_router():
    class AnotherTestProvider(Provider, metaclass=ProviderMeta):
        hello_router = provide_router(router)
        hello_router2 = provide_router(router2)

    app = App("test app", "0.1.0", LoggerProvider(), AnotherTestProvider())

    await app._resolve_container()

    assert app.routers is not None
    assert len(app.routers) == 2


@pytest.mark.asyncio
async def test_another_app_can_auto_wire_routers_from_different_providers():
    class AnotherTestProvider(Provider, metaclass=ProviderMeta):
        hello_router = provide_router(router)
        service = provide(Service, scope=Scope.APP)

    class AnotherTestProvider2(Provider, metaclass=ProviderMeta):
        hello_router2 = provide_router(router2)

    app = App("test app", "0.1.0", LoggerProvider(), AnotherTestProvider(), AnotherTestProvider2())

    await app._resolve_container()

    assert app.routers is not None
    assert len(app.routers) == 2


@pytest.mark.asyncio
async def test_app_can_start_and_handle_requests():
    """Test that the app can start and handle HTTP requests to registered routers."""

    class TestProvider(Provider, metaclass=ProviderMeta):
        service = provide(Service, scope=Scope.APP)
        hello_router = provide_router(router)
        hello_router2 = provide_router(router2)

    app = App("test app", "0.1.0", LoggerProvider(), TestProvider())

    # Start the app in non-blocking mode on a different port to avoid conflicts
    # The start() method now handles container resolution internally
    port = 8001
    await app.start(blocking=False, port=port)

    try:
        # Wait for the server to start
        max_retries = 30
        for i in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://127.0.0.1:{port}/router/")
                    if response.status_code == 200:
                        break
            except (httpx.ConnectError, httpx.ConnectTimeout):
                if i == max_retries - 1:
                    raise
                await asyncio.sleep(0.1)

        # Test first router
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:{port}/router/")
            assert response.status_code == 200
            assert response.json() == {"message": "Hello, World!"}

        # Test second router
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:{port}/router2/")
            assert response.status_code == 200
            assert response.json() == {"message": "Hello, World! 2"}

    finally:
        # Stop the server
        app.stop()


@pytest.mark.asyncio
async def test_app_can_auto_wire_middleware_with_dependency_injection():
    """Test that middleware can be auto-wired and can use dependency injection with complex dependency chains."""

    class TestProvider(Provider, metaclass=ProviderMeta):
        service = provide(Service, scope=Scope.APP)
        hello_router = provide_router(router)
        counter_middleware = provide_middleware(CounterHeaderMiddleware)

    app = App("test app", "0.1.0", LoggerProvider(), TestProvider())

    # Start the app in non-blocking mode - this handles container resolution internally
    port = 8002
    await app.start(blocking=False, port=port)

    try:
        # Wait for the server to start
        max_retries = 30
        for i in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://127.0.0.1:{port}/router/")
                    if response.status_code == 200:
                        break
            except (httpx.ConnectError, httpx.ConnectTimeout):
                if i == max_retries - 1:
                    raise
                await asyncio.sleep(0.1)

        # Make a request and check that the middleware adds the counter header
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:{port}/router/")
            assert response.status_code == 200
            assert response.json() == {"message": "Hello, World!"}

            # The middleware should add headers with counter and logger info
            assert "X-Counter" in response.headers
            assert "X-Logger-Logs" in response.headers

            # Since the route increments the counter, and service logs during init + increment
            first_counter = int(response.headers["X-Counter"])
            first_logs = int(response.headers["X-Logger-Logs"])
            assert first_counter >= 1
            assert first_logs >= 2  # At least init log + increment log

        # Make another request to verify the counter increments (app-scoped service)
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:{port}/router/")
            assert response.status_code == 200

            # Counter and logs should have incremented
            second_counter = int(response.headers["X-Counter"])
            second_logs = int(response.headers["X-Logger-Logs"])
            assert second_counter == first_counter + 1
            assert second_logs == first_logs + 1  # One more increment log

    finally:
        # Stop the server
        app.stop()


@pytest.mark.asyncio
async def test_start_and_stop_test_utilities():
    """Test the start_test() and stop_test() utilities work correctly."""

    class TestUtilitiesProvider(Provider, metaclass=ProviderMeta):
        service = provide(Service, scope=Scope.APP)
        hello_router = provide_router(router)

    app = App("Test API", "1.0.0", LoggerProvider(), TestUtilitiesProvider())

    try:
        # Test start_test utility
        returned_app = await start_test(app, port=9998)
        assert returned_app is app  # Should return the same app instance

        # Test that the app is working
        client = TestClient(app.app)
        response = client.get("/router/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"

    finally:
        # Test stop_test utility
        await stop_test(app)


@pytest.mark.asyncio
async def test_context_manager_utility():
    """Test the test() context manager utility works correctly."""

    class TestContextProvider(Provider, metaclass=ProviderMeta):
        service = provide(Service, scope=Scope.APP)
        hello_router = provide_router(router)

    app = App("Test Context API", "1.0.0", LoggerProvider(), TestContextProvider())

    # Test the context manager
    async with test(app, port=9997) as test_app:
        assert test_app is app  # Should yield the same app instance

        # Test that the app is working
        client = TestClient(test_app.app)
        response = client.get("/router/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"


# Global provider to test reuse across multiple tests
class SharedTestProvider(Provider, metaclass=ProviderMeta):
    scope = Scope.APP
    service = provide(Service, scope=Scope.APP)
    hello_router = provide_router(router)


@pytest.mark.asyncio
async def test_shared_provider_first_test():
    """Test using a shared provider - first test should work."""
    app = App("Shared Test 1", "1.0.0", LoggerProvider(), SharedTestProvider())

    async with test(app) as test_app:
        client = TestClient(test_app.app)
        response = client.get("/router/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"


@pytest.mark.asyncio
async def test_shared_provider_second_test():
    """Test using the same shared provider - second test should also work thanks to backup registry."""
    app = App("Shared Test 2", "1.0.0", LoggerProvider(), SharedTestProvider())

    async with test(app) as test_app:
        client = TestClient(test_app.app)
        response = client.get("/router/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"


@pytest.mark.asyncio
async def test_shared_provider_third_test_with_start_stop():
    """Test using the same shared provider with start_test/stop_test pattern."""
    app = App("Shared Test 3", "1.0.0", LoggerProvider(), SharedTestProvider())

    try:
        await start_test(app, port=9995)
        client = TestClient(app.app)
        response = client.get("/router/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"
    finally:
        await stop_test(app)
