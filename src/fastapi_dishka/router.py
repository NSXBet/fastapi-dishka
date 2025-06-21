from fastapi import APIRouter as FastAPIRouter
from dishka.integrations.fastapi import DishkaRoute
from typing import Any


class APIRouter(FastAPIRouter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize APIRouter with DishkaRoute as the default route class.

        Args:
            *args: Positional arguments passed to FastAPI's APIRouter
            **kwargs: Keyword arguments passed to FastAPI's APIRouter,
                     with route_class defaulting to DishkaRoute for dependency injection.
        """
        # Set DishkaRoute as the default route class if not specified
        if "route_class" not in kwargs:
            kwargs["route_class"] = DishkaRoute

        super().__init__(*args, **kwargs)
