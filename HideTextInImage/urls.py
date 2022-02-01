from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name="home"),
    path('normalUpload',views.normalUpload,name="normalUpload"),
    path('micro',views.micro,name="micro"),
]