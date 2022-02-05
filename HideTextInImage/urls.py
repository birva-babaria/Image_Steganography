from django.urls import path
from . import views


urlpatterns = [
    path('',views.home,name="home"),
    path('text', views.text, name="text"),
    path('encode', views.encode, name="encode"),
    path('decode', views.decode, name="decode"),
    # path('micro', views.micro, name="micro"),
]
