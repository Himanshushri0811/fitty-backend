from django.urls import path, include
from accounts.views import HealthCheckView

urlpatterns = [
    # path("admin/", admin.site.urls), # Disabled in Pure Mongo
    path("api/health/db/", HealthCheckView.as_view(), name='db_health'),
    path("api/accounts/", include("accounts.urls")),
    path("api/ai/", include("ai.urls")),
    path("api/explore/", include("explore.urls")),
    # path("api/admin-panel/", include("admin_panel.urls")),
    # path('api/support/', include('support.urls')),
    path('api/social/', include('social.urls')),
    path('api/gym/', include('gym_management.urls')),
]

# Serve media files in development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
