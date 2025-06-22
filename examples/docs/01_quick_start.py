from dishka import Scope, provide, FromDishka
from fastapi_dishka import App, APIRouter, provide_router, Provider


# 📋 Your service
class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}! 👋"


# 🛣️ Your router
router = APIRouter()


@router.get("/greet/{name}")
async def greet_endpoint(name: str, service: FromDishka[GreetingService]) -> dict[str, str]:
    return {"message": service.greet(name)}


# 🏭 Create your provider
class AppProvider(Provider):
    scope = Scope.APP

    greeting_service = provide(GreetingService, scope=Scope.APP)
    greeting_router = provide_router(router)


# 🚀 Launch your app
app = App("My Awesome App 🎉", "1.0.0", AppProvider())

if __name__ == "__main__":
    import asyncio

    asyncio.run(app.start())
