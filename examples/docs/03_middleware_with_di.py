from dishka import Scope, provide, FromDishka
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_dishka import App, APIRouter, Middleware, provide_router, provide_middleware, Provider


class AuthService:
    def is_authenticated(self, request: Request) -> bool:
        # Simple check for Authorization header
        return request.headers.get("Authorization") is not None


class AuthMiddleware(Middleware):
    async def dispatch(self, request, call_next):
        # 💉 Inject services right into your middleware!
        auth_service = await self.get_dependency(request, AuthService)

        if not auth_service.is_authenticated(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        return await call_next(request)


# Create a simple router for testing
router = APIRouter()


@router.get("/protected")
async def protected_endpoint():
    return {"message": "You are authenticated!"}


class SecurityProvider(Provider):
    scope = Scope.APP

    # 🛡️ Provide our auth service
    auth_service = provide(AuthService, scope=Scope.APP)

    # 🔧 Register middleware and router with DI support
    auth_middleware = provide_middleware(AuthMiddleware)
    api_router = provide_router(router)


app = App("Middleware DI Demo", "1.0.0", SecurityProvider())

if __name__ == "__main__":
    print("Try: curl -H 'Authorization: Bearer token' http://localhost:8000/protected")
    app.start_sync()
