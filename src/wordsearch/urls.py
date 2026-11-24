from django.urls import path

from . import views

app_name = "wordsearch"

urlpatterns = [
    path("", views.maker, name="maker"),
    path("solve/", views.solver, name="solver"),
]
