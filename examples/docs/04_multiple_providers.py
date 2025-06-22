from dishka import Scope, provide, FromDishka
from fastapi_dishka import App, APIRouter, provide_router, Provider


class UserService:
    def get_users(self):
        return [{"id": 1, "name": "Alice"}]


class PostService:
    def get_posts(self):
        return [{"id": 1, "title": "Hello World"}]


# Create routers
user_router = APIRouter(prefix="/users")
post_router = APIRouter(prefix="/posts")


@user_router.get("/")
async def get_users(service: FromDishka[UserService]):
    return {"users": service.get_users()}


@post_router.get("/")
async def get_posts(service: FromDishka[PostService]):
    return {"posts": service.get_posts()}


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

if __name__ == "__main__":
    app.start_sync()
