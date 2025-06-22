import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi_dishka.app import App
from fastapi_dishka.middleware import Middleware
from fastapi_dishka.providers import provide_middleware, provide_router
from fastapi_dishka.router import APIRouter


def _restore_from_backup_if_needed() -> None:
    """Restore from backup registries if main registries are empty but backups exist."""
    from fastapi_dishka.providers import (
        _router_registry,
        _middleware_registry,
        _router_backup,
        _middleware_backup,
    )

    # Only restore if registries are empty but backups exist
    if not _router_registry and _router_backup:
        _router_registry.extend(_router_backup)

    if not _middleware_registry and _middleware_backup:
        _middleware_registry.extend(_middleware_backup)


async def start_test(app: App, host: str = "127.0.0.1", port: int = 8000) -> App:
    """
    Start an App instance for testing purposes.

    This utility function handles all the complexity of starting a server
    for testing, including necessary delays for proper async cleanup.

    Args:
        app: The App instance to start
        host: Host to bind to (default: "127.0.0.1")
        port: Port to bind to (default: 8000)

    Returns:
        The same App instance, ready for testing

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_my_app():
            app = App("Test API", "1.0.0", MyProvider())

            try:
                await start_test(app, port=9999)
                client = TestClient(app.app)
                response = client.get("/hello")
                assert response.status_code == 200
            finally:
                await stop_test(app)
        ```
    """
    # Restore from backup if needed (for provider reuse across tests)
    _restore_from_backup_if_needed()

    await app.start(blocking=False, host=host, port=port)
    # Give the server a moment to fully start
    await asyncio.sleep(0.1)
    return app


async def stop_test(app: App) -> None:
    """
    Stop an App instance that was started with start_test().

    This utility function handles all the complexity of stopping a test server,
    including necessary delays for proper async cleanup.

    Args:
        app: The App instance to stop

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_my_app():
            app = App("Test API", "1.0.0", MyProvider())

            try:
                await start_test(app, port=9999)
                # Your tests here
            finally:
                await stop_test(app)
        ```
    """
    app.stop()
    # Give the server a moment to fully stop
    await asyncio.sleep(0.1)


@asynccontextmanager
async def test(app: App, host: str = "127.0.0.1", port: int = 8000) -> AsyncGenerator[App, None]:
    """
    Context manager for testing FastAPI-Dishka applications.

    This context manager handles all the complexity of setting up the app
    for testing with TestClient, including container resolution and cleanup.

    Args:
        app: The App instance to test
        host: Host to bind to (for compatibility, not used with TestClient)
        port: Port to bind to (for compatibility, not used with TestClient)

    Yields:
        The same App instance, ready for testing with TestClient

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_my_app():
            app = App("Test API", "1.0.0", MyProvider())

            async with test(app) as test_app:
                client = TestClient(test_app.app)
                response = client.get("/hello")
                assert response.status_code == 200
        ```
    """
    # Restore from backup if needed (for provider reuse across tests)
    _restore_from_backup_if_needed()

    # For TestClient, we just need to resolve the container, not start a server
    await app._resolve_container()
    try:
        yield app
    finally:
        # Clean up the container
        await app.close()


__all__ = [
    "App",
    "APIRouter",
    "provide_router",
    "provide_middleware",
    "Middleware",
    "start_test",
    "stop_test",
    "test",
]
