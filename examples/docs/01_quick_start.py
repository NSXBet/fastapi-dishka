from dishka import Provider, Scope, provide, FromDishka
from fastapi_dishka import App, APIRouter, provide_router


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
