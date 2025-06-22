#!/usr/bin/env python3
"""
Example demonstrating FastAPI-Dishka router auto-registration.

This example shows how to:
1. Create routers with endpoints that use dependency injection
2. Use provide_router to auto-register them
3. Create an App that automatically includes all registered routers
4. Start the server with dependency injection working
"""

import asyncio
from dishka import FromDishka, provide, Scope

from fastapi_dishka import App, provide_router, APIRouter, Provider


class Logger:
    """Simple logger service."""

    def __init__(self):
        self.logs = []

    def info(self, message: str):
        log_entry = f"[INFO] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def get_logs(self):
        return self.logs.copy()


class UserService:
    """Service for user-related operations."""

    def __init__(self, logger: FromDishka[Logger]):
        self.logger = logger
        self.users = ["alice", "bob", "charlie"]
        self.logger.info("UserService initialized")

    def get_all_users(self):
        self.logger.info("Getting all users")
        return self.users

    def get_user_by_id(self, user_id: int):
        self.logger.info(f"Getting user with ID: {user_id}")
        if 0 <= user_id < len(self.users):
            return {"user_id": user_id, "name": self.users[user_id]}
        return {"error": "User not found"}


class ProductService:
    """Service for product-related operations."""

    def __init__(self, logger: FromDishka[Logger]):
        self.logger = logger
        self.products = ["laptop", "mouse", "keyboard"]
        self.logger.info("ProductService initialized")

    def get_all_products(self):
        self.logger.info("Getting all products")
        return self.products

    def get_product_by_id(self, product_id: int):
        self.logger.info(f"Getting product with ID: {product_id}")
        if 0 <= product_id < len(self.products):
            return {"product_id": product_id, "name": self.products[product_id]}
        return {"error": "Product not found"}


# Create routers with dependency injection
users_router = APIRouter(prefix="/users", tags=["users"])
products_router = APIRouter(prefix="/products", tags=["products"])


@users_router.get("/")
def list_users(user_service: FromDishka[UserService]):
    users = user_service.get_all_users()
    return {"users": users}


@users_router.get("/{user_id}")
def get_user(user_id: int, user_service: FromDishka[UserService]):
    return user_service.get_user_by_id(user_id)


@products_router.get("/")
def list_products(product_service: FromDishka[ProductService]):
    products = product_service.get_all_products()
    return {"products": products}


@products_router.get("/{product_id}")
def get_product(product_id: int, product_service: FromDishka[ProductService]):
    return product_service.get_product_by_id(product_id)


# Create providers that supply dependencies and auto-register routers
class CoreProvider(Provider):
    """Provider for core dependencies."""

    scope = Scope.APP

    logger = provide(Logger, scope=Scope.APP)


class UserProvider(Provider):
    """Provider for user-related dependencies."""

    scope = Scope.APP
    user_service = provide(UserService, scope=Scope.APP)
    users_router = provide_router(users_router)


class ProductProvider(Provider):
    """Provider for product-related dependencies."""

    scope = Scope.APP
    product_service = provide(ProductService, scope=Scope.APP)
    products_router = provide_router(products_router)


async def main():
    """Main function demonstrating the app setup and usage."""
    # Create the app with multiple providers
    app = App(
        "FastAPI-Dishka Example",
        "1.0.0",
        CoreProvider(),
        UserProvider(),
        ProductProvider(),
        description="Example showing auto-router registration with Dishka dependency injection",
    )

    print("🚀 Starting server on http://127.0.0.1:8000")
    print("Available endpoints:")
    print("  - GET /users/ - List all users (with DI)")
    print("  - GET /users/{user_id} - Get specific user (with DI)")
    print("  - GET /products/ - List all products (with DI)")
    print("  - GET /products/{product_id} - Get specific product (with DI)")
    print("  - GET /docs - Swagger UI documentation")
    print("\nPress Ctrl+C to stop the server")

    # Start the server - this handles everything: container resolution, router registration, etc.
    await app.start(blocking=True, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    asyncio.run(main())
