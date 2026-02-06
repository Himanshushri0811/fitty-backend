from rest_framework import serializers
from .models import WaterIntake, DailyIntake, DailyPlan, PlanItem, Exercise, WorkoutDay, DayExercise

class DailyIntakeSerializer(serializers.Serializer):
    glasses = serializers.IntegerField(default=0)
    total_ml = serializers.IntegerField(default=0)
    last_drink_at = serializers.CharField(required=False)

class WaterIntakeSerializer(serializers.Serializer):
    records = serializers.DictField(child=DailyIntakeSerializer())

class PlanItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    time = serializers.CharField()
    title = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    coach_note = serializers.CharField(required=False, allow_blank=True)

class DailyPlanSerializer(serializers.Serializer):
    date = serializers.CharField()
    items = PlanItemSerializer(many=True)
    coach_message = serializers.CharField()

class ExerciseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    target_muscle = serializers.CharField(required=False, allow_blank=True)
    demo_video_url = serializers.CharField(required=False, allow_blank=True)
    pose_config = serializers.DictField(required=False)
