from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from portal.forms import LoginForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(
        template_name="registration/login.html",
        authentication_form=LoginForm
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("portal.urls")),
]
