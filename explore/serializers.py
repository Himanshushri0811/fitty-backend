from rest_framework import serializers

class GymSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    rating = serializers.FloatField(read_only=True)
    price_range_min = serializers.FloatField()
    price_range_max = serializers.FloatField()
    thumbnail = serializers.CharField(required=False, allow_null=True)

class TrainerSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    specialization = serializers.CharField()
    experience_years = serializers.IntegerField()

class EventSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    start_time = serializers.DateTimeField()
    status = serializers.CharField()
