from django.urls import path
from .views import ContactMessageView, PublicLiveChatView, AgentLiveChatView

urlpatterns = [
    path('contact/', ContactMessageView.as_view(), name='contact_message'),
]
