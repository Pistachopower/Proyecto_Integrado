from django.urls import path
from .api_views import *

urlpatterns = [
    path("productos", mostrar_productos, name="mostrar_productos"),

]