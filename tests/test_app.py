from fastapi import APIRouter
from dishka import Provider

from fastapi_dishka import App, provide_router

import pytest

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
