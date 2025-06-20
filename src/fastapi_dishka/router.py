from fastapi import APIRouter as FastAPIRouter
from dishka.integrations.fastapi import DishkaRoute


class APIRouter(FastAPIRouter):
    def __init__(self, *args, **kwargs):
        kwargs["route_class"] = DishkaRoute
        super().__init__(*args, **kwargs)
