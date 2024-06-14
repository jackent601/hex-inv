from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("testVis", views.testVis, name="testVis"),
]