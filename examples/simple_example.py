#!/usr/bin/env python3
"""
Example demonstrating FastAPI-Dishka router auto-registration.

This example shows how to:
1. Create routers with endpoints
2. Use provide_router to auto-register them
3. Create an App that automatically includes all registered routers
4. Start the server
"""

import asyncio
from fastapi import APIRouter
from dishka import Provider

from fastapi_dishka import App, provide_router

# Create some example routers
users_router = APIRouter(prefix="/users", tags=["users"])
products_router = APIRouter(prefix="/products", tags=["products"])


@users_router.get("/")
def list_users():
    return {"users": ["alice", "bob", "charlie"]}


@users_router.get("/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}"}


@products_router.get("/")
def list_products():
    return {"products": ["laptop", "mouse", "keyboard"]}


@products_router.get("/{product_id}")
def get_product(product_id: int):
    return {"product_id": product_id, "name": f"Product {product_id}"}


# Create providers that auto-register the routers
class UsersProvider(Provider):
    """Provider for user-related dependencies."""

    users_router = provide_router(users_router)


class ProductsProvider(Provider):
    """Provider for product-related dependencies."""

    products_router = provide_router(products_router)


async def main():
    """Main function demonstrating the app setup and usage."""
    # Create the app with multiple providers
    app = App(
        "FastAPI-Dishka Example",
        "1.0.0",
        UsersProvider(),
        ProductsProvider(),
        description="Example showing auto-router registration with Dishka",
    )

    # Resolve the container (this registers all routers)
    await app._resolve_container()

    print(f"✅ App created with {len(app.routers)} routers automatically registered:")
    for router in app.routers:
        print(f"  - Router with prefix: {router.prefix}")

    print("\n🚀 Starting server on http://127.0.0.1:8000")
    print("Available endpoints:")
    print("  - GET /users/ - List all users")
    print("  - GET /users/{user_id} - Get specific user")
    print("  - GET /products/ - List all products")
    print("  - GET /products/{product_id} - Get specific product")
    print("  - GET /docs - Swagger UI documentation")
    print("\nPress Ctrl+C to stop the server")

    # Start the server (blocking mode)
    app.start(blocking=True, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    asyncio.run(main())
