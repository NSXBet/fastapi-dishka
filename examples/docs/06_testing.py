"""
🧪 Testing Example

This shows how to test fastapi-dishka applications with proper cleanup.

Usage:
    pytest examples/docs/06_testing.py -v
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from dishka import Scope, provide, FromDishka
from fastapi_dishka import App, APIRouter, provide_router, start_test, stop_test, test, Provider


# Let's see the typical hello world example you'd expect in every open source project!


class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}! 👋"


# Create router
hello_router = APIRouter()


@hello_router.get("/hello/{name}")
async def hello_endpoint(name: str, service: FromDishka[GreetingService]) -> dict:
    return {"message": service.greet(name)}


# Create provider
class HelloProvider(Provider):
    scope = Scope.APP
    greeting_router = provide_router(hello_router)
    greeting_service = provide(GreetingService, scope=Scope.APP)


@pytest.mark.asyncio
async def test_hello_world():
    """The classic hello world test everyone expects to see."""
    app = App("Hello World API", "1.0.0", HelloProvider())

    try:
        # 🚀 Use start_test() for clean async server startup
        await start_test(app, port=9999)

        client = TestClient(app.app)
        response = client.get("/hello/World")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World! 👋"
    finally:
        # 🧹 Use stop_test() for clean async server shutdown
        await stop_test(app)


@pytest.mark.asyncio
async def test_hello_world_with_context_manager():
    """The cleanest way to test - using the context manager! 🎯"""
    app = App("Hello World API", "1.0.0", HelloProvider())

    # 🎯 Ultra-clean testing with context manager
    async with test(app) as test_app:
        client = TestClient(test_app.app)
        response = client.get("/hello/World")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World! 👋"
    # 🧹 Cleanup happens automatically!


if __name__ == "__main__":
    print("🧪 FastAPI-Dishka Testing Examples")
    print("Run with: pytest examples/docs/06_testing.py -v")
