from django.urls import path
from .views import CreateSubscriptionOrderView, VerifySubscriptionView, RazorpayWebhookView

urlpatterns = [
    path('order/create/', CreateSubscriptionOrderView.as_view(), name='sub-order-create'),
    path('verify/', VerifySubscriptionView.as_view(), name='sub-verify'),
    path('webhook/', RazorpayWebhookView.as_view(), name='sub-webhook'),
]
