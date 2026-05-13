"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from sportscio import views
from django.views.generic import RedirectView

#Project Level Url Patterns. Django will look here first
urlpatterns = [
    path("", RedirectView.as_view(url='/login/', permanent=False)), #default page 
    path("sportscio/", include("sportscio.urls")), #include sportscio app urls
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"), #uses built in django login view with our template
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),#uses built in django logout view
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG and not getattr(settings, "USE_S3", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)