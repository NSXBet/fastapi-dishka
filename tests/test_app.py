import asyncio
import time
from fastapi import APIRouter
from dishka import Provider
import httpx
import pytest

from fastapi_dishka import App, provide_router

router = APIRouter(prefix="/router")
router2 = APIRouter(prefix="/router2")


@router.get("/")
def hello_world():
    return {"message": "Hello, World!"}


@router2.get("/")
def hello_world2():
    return {"message": "Hello, World! 2"}


@pytest.mark.asyncio
async def test_app_can_auto_wire_routers():
    class TestProvider(Provider):
        hello_router = provide_router(router)

    app = App("test app", "0.1.0", TestProvider())

    await app._resolve_container()

    assert app.routers is not None
    assert len(app.routers) == 1


@pytest.mark.asyncio
async def test_another_app_can_auto_wire_routers():
    class AnotherTestProvider(Provider):
        hello_router = provide_router(router)

    app = App("test app", "0.1.0", AnotherTestProvider())

    await app._resolve_container()

    assert app.routers is not None
    assert len(app.routers) == 1


@pytest.mark.asyncio
async def test_another_app_can_auto_wire_more_than_one_router():
    class AnotherTestProvider(Provider):
        hello_router = provide_router(router)
        hello_router2 = provide_router(router2)

    app = App("test app", "0.1.0", AnotherTestProvider())

    await app._resolve_container()

    assert app.routers is not None
    assert len(app.routers) == 2


@pytest.mark.asyncio
async def test_another_app_can_auto_wire_routers_from_different_providers():
    class AnotherTestProvider(Provider):
        hello_router = provide_router(router)

    class AnotherTestProvider2(Provider):
        hello_router2 = provide_router(router2)

    app = App("test app", "0.1.0", AnotherTestProvider(), AnotherTestProvider2())

    await app._resolve_container()

    assert app.routers is not None
    assert len(app.routers) == 2


@pytest.mark.asyncio
async def test_app_can_start_and_handle_requests():
    """Test that the app can start and handle HTTP requests to registered routers."""

    class TestProvider(Provider):
        hello_router = provide_router(router)
        hello_router2 = provide_router(router2)

    app = App("test app", "0.1.0", TestProvider())
    await app._resolve_container()

    # Start the app in non-blocking mode on a different port to avoid conflicts
    port = 8001
    app.start(blocking=False, port=port)

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
