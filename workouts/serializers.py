from rest_framework import serializers
from .models import WorkoutPlan, DailyRoutine, WorkoutExercise, Exercise

class ExerciseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    video_url = serializers.CharField(required=False)
    difficulty = serializers.CharField(required=False)
    target_muscle_group = serializers.CharField(required=False)
    posture_config = serializers.DictField(required=False)

class WorkoutExerciseSerializer(serializers.Serializer):
    exercise_name = serializers.CharField()
    sets = serializers.IntegerField()
    reps = serializers.CharField()
    rest_time_seconds = serializers.IntegerField(required=False)
    notes = serializers.CharField(required=False)
    video_url = serializers.CharField(required=False, allow_blank=True) # Computed field if needed

class DailyRoutineSerializer(serializers.Serializer):
    day_name = serializers.CharField()
    focus_area = serializers.CharField(required=False)
    exercises = WorkoutExerciseSerializer(many=True)

class WorkoutPlanSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    goal = serializers.CharField()
    days_per_week = serializers.IntegerField()
    routines = DailyRoutineSerializer(many=True)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
