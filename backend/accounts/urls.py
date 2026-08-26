from django.urls import path

from .views import CurrentUserView, RegistrationView


urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]