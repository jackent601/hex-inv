from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("geopd", views.geopd, name="geopd"),
    path("hexpd", views.hexpd, name="hexpd"),
    
    path("geons", views.geons, name="geons"),
    path("hexns", views.hexns, name="hexns"),
]