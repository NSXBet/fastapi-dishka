from dishka import Scope, provide, FromDishka
from fastapi_dishka import App, APIRouter, provide_router, Provider

# Create the routers
users_router = APIRouter(prefix="/users")
posts_router = APIRouter(prefix="/posts")
comments_router = APIRouter(prefix="/comments")


@users_router.get("/")
async def get_users():
    return {"users": ["Alice", "Bob"]}


@posts_router.get("/")
async def get_posts():
    return {"posts": ["Post 1", "Post 2"]}


@comments_router.get("/")
async def get_comments():
    return {"comments": ["Comment 1", "Comment 2"]}


class MyProvider(Provider):
    scope = Scope.APP
    # ✨ These routers register themselves automatically
    users_router = provide_router(users_router)
    posts_router = provide_router(posts_router)
    comments_router = provide_router(comments_router)


app = App("Auto-Router Demo", "1.0.0", MyProvider())

if __name__ == "__main__":
    app.start_sync()
