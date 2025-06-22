from dishka import Scope, provide
from fastapi_dishka import App, APIRouter, provide_router, Provider

# Simple example service and router
router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Server management demo"}


class AppProvider(Provider):
    scope = Scope.APP
    main_router = provide_router(router)


app = App("Server Demo", "1.0.0", AppProvider())

# 🔥 Blocking mode (great for production)
# app.start_sync(host="0.0.0.0", port=8080)

# 🧵 Non-blocking mode (perfect for testing)
# app.start_sync(blocking=False, port=8081)
# ... do other stuff ...
# app.stop()  # 🛑 Graceful shutdown

# ⚡ Async mode
# await app.start(host="127.0.0.1", port=8082)

if __name__ == "__main__":
    print("Choose server mode:")
    print("1. Blocking mode")
    print("2. Non-blocking mode (5 seconds)")
    print("3. Default")

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        app.start_sync(host="0.0.0.0", port=8080)
    elif choice == "2":
        print("Starting in non-blocking mode for 5 seconds...")
        app.start_sync(blocking=False, port=8081)
        import time

        time.sleep(5)
        app.stop()
        print("Server stopped")
    else:
        app.start_sync()
