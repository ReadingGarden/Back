import logging
from django.urls import path

from ninja import NinjaAPI

from auths.views import router as auth_router
from garden.views import router as garden_router
from book.views import router as book_router

logger = logging.getLogger("django.server")

api_v1 = NinjaAPI(
    version="1.0.0",
    title="book BE",
    description="API Set"
)

api_v1.add_router("auth", auth_router)
api_v1.add_router("garden", garden_router)
api_v1.add_router("book", book_router)

urlpatterns = [
    path("api/v1/", api_v1.urls)
]