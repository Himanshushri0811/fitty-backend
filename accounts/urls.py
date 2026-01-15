from django.urls import path
from .views import SignupAPIView, LoginAPIView, ProfileView, VerifyPaymentAPIView, HealthCheckView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('signup/', SignupAPIView.as_view(), name='signup'),
    path('signup/gym-owner/', SignupAPIView.as_view(), name='gym-owner-signup'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('payments/verify/', VerifyPaymentAPIView.as_view(), name='verify-payment'),
]
