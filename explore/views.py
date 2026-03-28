from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Gym, Trainer, Event, Challenge
from .serializers import GymSerializer, TrainerSerializer, EventSerializer

class GymListView(APIView):
    def get(self, request):
        gyms = Gym.objects(is_active=True)
        return Response(GymSerializer(gyms, many=True).data)

class TrainerListView(APIView):
    def get(self, request):
        trainers = Trainer.objects.all()
        return Response(TrainerSerializer(trainers, many=True).data)

class EventListView(APIView):
    def get(self, request):
        events = Event.objects.all()
        return Response(EventSerializer(events, many=True).data)
