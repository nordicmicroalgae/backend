"""nordicmicroalgae URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    # Admin site routes
    path(
        'admin/password_reset/',
        auth_views.PasswordResetView.as_view(
            extra_context={'site_header': admin.site.site_header}
        ),
        name='admin_password_reset',
    ),
    path(
        'admin/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            extra_context={'site_header': admin.site.site_header}
        ),
        name='password_reset_done',
    ),
    path(
        'admin/password_reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            extra_context={'site_header': admin.site.site_header}
        ),
        name='password_reset_confirm',
    ),
    path(
        'admin/password_reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            extra_context={'site_header': admin.site.site_header}
        ),
        name='password_reset_complete',
    ),
    path('admin/', admin.site.urls),
    # REST API routes
    path('api/', include('pages.urls')),
    path('api/', include('taxa.urls')),
    path('api/', include('facts.urls')),
    path('api/', include('media.urls')),
    path('api/', include('contributors.urls')),
    path('api/', include('openapi.urls')),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
