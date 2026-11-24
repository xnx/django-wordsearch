from django.urls import include, path

urlpatterns = [path("wordsearch/", include("wordsearch.urls"))]
