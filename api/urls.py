from django.urls import path
from . import views

urlpatterns = [
    path("", views.get_data, name="data_get"),
    path("auth/register", views.register_user, name="register"),
    path("auth/login", views.login_user),
    path("api/users/<str:id>", views.get_user),

    path("api/organisations", views.get_and_create_org),
    path("api/organisations/<str:orgId>", views.get_organisation),
    path("api/organisations/<str:orgId>/users", views.add_user_to_org)

]
