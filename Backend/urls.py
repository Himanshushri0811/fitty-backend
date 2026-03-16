from django.urls import path, include
from accounts.views import HealthCheckView
from django.http import JsonResponse

def minimal_health(request):
    return JsonResponse({"status": "minimal_ok", "note": "direct_from_urls"})

urlpatterns = [
    path("", minimal_health), # Extremely minimal root check
    # path("admin/", admin.site.urls), # Disabled in Pure Mongo
    path("api/health/", HealthCheckView.as_view(), name='health'),
    path("api/accounts/", include("accounts.urls")),
    path("api/ai/", include("ai.urls")),
    path("api/missions/", include("missions.urls")),
    # path("api/admin-panel/", include("admin_panel.urls")),
    path('api/support/', include('support.urls')),
    path('api/social/', include('social.urls')),
    path('api/gym/', include('gym_management.urls')),
    path('api/fitness/', include('fitness.urls')),
    path('api/diet/', include('diet.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/workouts/', include('workouts.urls')),
    path('api/fitty-ai/', include('fitty_ai.urls')),
]

# Serve media files in development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
