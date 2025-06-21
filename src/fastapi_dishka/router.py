from typing import Any

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter as FastAPIRouter


class APIRouter(FastAPIRouter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[explicit-any]
        """
        Initialize APIRouter with DishkaRoute as the default route class.

        Args:
            *args: Positional arguments passed to FastAPI's APIRouter
            **kwargs: Keyword arguments passed to FastAPI's APIRouter,
                     with route_class defaulting to DishkaRoute for dependency injection.
        """
        # Set DishkaRoute as the default route class if not specified
        route_class_key: str = "route_class"
        if route_class_key not in kwargs:  # type: ignore[misc]
            kwargs[route_class_key] = DishkaRoute  # type: ignore[misc]

        super().__init__(*args, **kwargs)  # type: ignore[misc]
