# 🚀 fastapi-dishka

[![codecov](https://codecov.io/gh/NSXBet/fastapi-dishka/graph/badge.svg?token=83VQ7PMJ1L)](https://codecov.io/gh/NSXBet/fastapi-dishka)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-96%25%20coverage-brightgreen.svg)](https://github.com/NSXBet/fastapi-dishka)

> 🍽️ **Serve your FastAPI dependencies with style!** A delightful integration between FastAPI and Dishka that makes dependency injection feel like a five-star dining experience.

## ✨ What is this magic?

**fastapi-dishka** bridges the gap between [FastAPI](https://fastapi.tiangolo.com/) and [Dishka](https://github.com/reagento/dishka), bringing you:

- 🔄 **Auto-registration** - Routers and middleware register themselves like magic
- 🎯 **Provider-first design** - Your providers are first-class citizens
- 🧩 **Seamless integration** - Works with existing FastAPI and Dishka code
- 🚀 **Zero boilerplate** - Less setup, more building awesome stuff
- 🔒 **Type-safe** - Full type hints and mypy support
- ⚡ **High performance** - Built on FastAPI and Dishka's solid foundations

## 🛠️ Installation

Get started in seconds:

```bash
pip install fastapi-dishka
```

Or if you're feeling fancy with poetry:

```bash
poetry add fastapi-dishka
```

## 🎬 Quick Start

Here's how easy it is to get rolling:

```python
from dishka import Scope, provide, FromDishka
from fastapi_dishka import App, APIRouter, provide_router, Provider

# 📦 Create your service
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}! 👋"

# 🛣️ Create your router
router = APIRouter(prefix="/api")

@router.get("/greet/{name}")
async def greet_endpoint(name: str, service: FromDishka[GreetingService]) -> dict:
    return {"message": service.greet(name)}

# 🏭 Create your provider
class AppProvider(Provider):
    scope = Scope.APP

    # 🎯 Auto-register the router
    greeting_router = provide_router(router)

    # 📋 Provide your services
    greeting_service = provide(GreetingService, scope=Scope.APP)

# 🚀 Launch your app
app = App("My Awesome API", "1.0.0", AppProvider())

if __name__ == "__main__":
    app.start_sync()  # 🔥 Your API is now running!
```

That's it! Your API is running with auto-registered routes and dependency injection. 🎉

## 🎭 Features & Examples

### 🔄 Auto-Router Registration

Say goodbye to manually registering every router:

```python
from fastapi_dishka import provide_router, Provider

class MyProvider(Provider):
    # ✨ These routers register themselves automatically
    users_router = provide_router(users_router)
    posts_router = provide_router(posts_router)
    comments_router = provide_router(comments_router)
```

### 🛡️ Middleware with Dependency Injection

Create powerful middleware that can inject dependencies:

```python
from fastapi_dishka import Middleware, provide_middleware, Provider

class AuthMiddleware(Middleware):
    async def dispatch(self, request, call_next):
        # 💉 Inject services right into your middleware!
        auth_service = await self.get_dependency(request, AuthService)

        if not auth_service.is_authenticated(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        return await call_next(request)

class SecurityProvider(Provider):
    scope = Scope.APP
    auth_service = provide(AuthService, scope=Scope.APP)

    # 🛡️ Auto-register middleware with DI support
    auth_middleware = provide_middleware(AuthMiddleware)
```

### 🏗️ Multiple Providers

Organize your code with multiple providers:

```python
from fastapi_dishka import Provider

# 👤 User-related stuff
class UserProvider(Provider):
    scope = Scope.APP
    user_router = provide_router(user_router)
    user_service = provide(UserService, scope=Scope.APP)

# 📝 Post-related stuff
class PostProvider(Provider):
    scope = Scope.APP
    post_router = provide_router(post_router)
    post_service = provide(PostService, scope=Scope.APP)

# 🚀 Combine them all
app = App("Blog API", "2.0.0", UserProvider(), PostProvider())
```

### 🌐 Server Management

Full control over your server lifecycle:

```python
# 🔥 Blocking mode (great for production)
app.start_sync(host="0.0.0.0", port=8080)

# 🧵 Non-blocking mode (perfect for testing)
app.start_sync(blocking=False, port=8081)
# ... do other stuff ...
app.stop()  # 🛑 Graceful shutdown

# ⚡ Async mode
await app.start(host="127.0.0.1", port=8082)
```

## 🏗️ Architecture

**fastapi-dishka** follows a provider-first design:

```
📦 Your App
├── 🏭 Providers (define what you have)
│   ├── 🛣️  Router providers (auto-register routes)
│   ├── 🛡️  Middleware providers (auto-register middleware)
│   └── 📋 Service providers (your business logic)
├── 🔄 Auto-registration (happens magically)
└── 🚀 FastAPI App (ready to serve)
```

## 🎛️ Provider Options

**fastapi-dishka** gives you flexibility in how you define your providers. You have two options:

### Option 1: Use fastapi-dishka Provider (Recommended)

```python
from fastapi_dishka import Provider

class MyProvider(Provider):
    scope = Scope.APP
    # Your provider methods here...
```

This is the recommended approach as it's specifically designed for fastapi-dishka integration.

### Option 2: Use dishka Provider with fastapi-dishka metaclass

```python
from dishka import Provider
from fastapi_dishka import FastAPIDishkaProviderMeta

class MyProvider(Provider, metaclass=FastAPIDishkaProviderMeta):
    scope = Scope.APP
    # Your provider methods here...
```

This approach allows you to use dishka's Provider directly while still getting fastapi-dishka's auto-registration features through the metaclass.

Both approaches provide the same functionality - choose the one that fits your project's needs! 🎯

## 🧪 Testing

Testing is a breeze with multiple patterns and full async support! Let's start with the classic hello world test:

```python
import pytest
from fastapi.testclient import TestClient
from dishka import Scope, provide, FromDishka
from fastapi_dishka import App, APIRouter, provide_router, start_test, stop_test, test, Provider

class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}! 👋"

hello_router = APIRouter()

@hello_router.get("/hello/{name}")
async def hello_endpoint(name: str, service: FromDishka[GreetingService]) -> dict:
    return {"message": service.greet(name)}

class HelloProvider(Provider):
    scope = Scope.APP
    greeting_router = provide_router(hello_router)
    greeting_service = provide(GreetingService, scope=Scope.APP)
```

### 🎯 Pattern 1: Context Manager (Recommended!)

The cleanest and most convenient way to test:

```python
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
```

### 🔧 Pattern 2: Manual Start/Stop

For more control over the server lifecycle:

```python
@pytest.mark.asyncio
async def test_hello_world():
    """Manual server management with start_test/stop_test."""
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
```

### 🎭 Which Pattern to Choose?

- **🎯 Context Manager**: Perfect for most tests, cleanest syntax, automatic cleanup
- **🔧 Start/Stop**: Use when you need custom server lifecycle management or multiple test phases

Both patterns handle provider reuse correctly, so you can use the same providers across multiple tests! 🎉

## 🤝 Contributing

We love contributions! Here's how to get started:

### 🚀 Quick Setup

```bash
# 📥 Clone the repo
git clone https://github.com/NSXBet/fastapi-dishka.git
cd fastapi-dishka

# 🐍 Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 📦 Install dependencies
pip install -e ".[dev]"
```

### 🧪 Running Tests

We maintain 96%+ test coverage (we're a bit obsessed 😅):

```bash
# 🏃‍♂️ Run all tests
make test

# 📊 Check coverage
make coverage

# 🔍 Lint your code
make lint

# ✨ Format your code
make format
```

### 🎯 Development Standards

- ✅ **Type Safety**: We love type hints and use mypy
- 🧪 **Test Coverage**: Keep it above 95%
- 📚 **Documentation**: Update docs for new features
- 🎨 **Code Style**: We use ruff and flake8
- 🚀 **Provider-First**: Make providers first-class citizens

### 💡 Ideas for Contributions

- 🔌 Additional integrations (SQLAlchemy, Redis, etc.)
- 📚 More examples and tutorials
- 🐛 Bug fixes and performance improvements
- 📖 Documentation improvements
- 🧪 More test coverage (can we hit 99%? 😏)

## 🐛 Issues & Questions

Found a bug? Have a question? Want to suggest a feature?

- 🐛 [Report bugs](https://github.com/NSXBet/fastapi-dishka/issues/new?labels=bug)
- 💡 [Request features](https://github.com/NSXBet/fastapi-dishka/issues/new?labels=enhancement)
- ❓ [Ask questions](https://github.com/NSXBet/fastapi-dishka/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- 🚀 [FastAPI](https://fastapi.tiangolo.com/) - For making APIs fun again
- 🍽️ [Dishka](https://github.com/reagento/dishka) - For elegant dependency injection
- ❤️ All our contributors and users

## ⭐ Show Your Support

If you like this project, please consider giving it a star! It helps others discover fastapi-dishka and motivates us to keep improving it.

---

<div align="center">

**Made with ❤️ and lots of ☕**

_Happy coding! 🚀_

</div>
