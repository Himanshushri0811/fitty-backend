from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import send_contact_email


class ContactView(APIView):
    def post(self, request):
        send_contact_email(
            request.data.get("subject", "No Subject"),
            request.data.get("message", ""),
            request.data.get("email", ""),
            request.data.get("name", "Anonymous")
        )
        return Response({"message": "Mail sent"})
