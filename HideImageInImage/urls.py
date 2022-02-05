from django.urls import path
from . import views

urlpatterns = [
    path('image', views.image, name="image"),
    path('encodeImage', views.encodeImage, name="encodeImage"),
    path('decodeImage', views.decodeImage, name="decodeImage"),
]
