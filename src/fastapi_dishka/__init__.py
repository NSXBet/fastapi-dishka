"""FastAPI-Dishka Integration Library."""

# Testing utilities
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .app import App
from .middleware import Middleware
from .providers import Provider, provide_middleware, provide_router
from .router import APIRouter


async def start_test(app: App, host: str = "127.0.0.1", port: int = 8000) -> App:
    """
    Start an app in test mode with proper async handling.

    Args:
        app: The App instance to start
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8000)

    Returns:
        The same App instance for chaining
    """
    await app.start(blocking=False, host=host, port=port)

    # Give the server a moment to start up
    await asyncio.sleep(0.1)

    return app


async def stop_test(app: App) -> None:
    """
    Stop an app started with start_test().

    Args:
        app: The App instance to stop
    """
    app.stop()

    # Give the server a moment to clean up
    await asyncio.sleep(0.1)


@asynccontextmanager
async def test(app: App, host: str = "127.0.0.1", port: int = 8000) -> AsyncGenerator[App, None]:
    """
    Context manager for testing apps with automatic cleanup.

    Usage:
        async with test(app, port=9999) as test_app:
            # Use test_app for testing
            client = TestClient(test_app.app)
            # Test your endpoints

    Args:
        app: The App instance to test
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8000)

    Yields:
        The App instance ready for testing
    """
    # Resolve container if not already done
    if not app._container_resolved:
        await app._resolve_container()

    # Create TestClient directly - no need for actual server
    yield app

    # Cleanup happens automatically with TestClient


__all__ = [
    "App",
    "APIRouter",
    "Middleware",
    "Provider",
    "provide_router",
    "provide_middleware",
    "start_test",
    "stop_test",
    "test",
]
