from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import WaterIntake, DailyIntake, DailyPlan
from .serializers import DailyPlanSerializer
from .utils import generate_daily_plan
from datetime import datetime
import pytz

class WaterIntakeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_today_date_str(self):
        # Use a fixed timezone or user's timezone if available. 
        # For now, defaulting to Asia/Kolkata as per user metadata or generic logic.
        tz = pytz.timezone('Asia/Kolkata')
        return datetime.now(tz).strftime('%Y-%m-%d')

    def get(self, request):
        user = request.user
        if user.role != 'USER':
             return Response({"error": "This feature is for Users only"}, status=403)

        try:
            water_intake = WaterIntake.objects.get(user=user)
        except WaterIntake.DoesNotExist:
            water_intake = WaterIntake(user=user, records={})
            water_intake.save()

        today_str = self.get_today_date_str()
        
        # Get today's record, or initialize default
        today_data = water_intake.records.get(today_str, DailyIntake(glasses=0, total_ml=0))
        
        return Response({
            "date": today_str,
            "glasses": today_data.glasses,
            "total_ml": today_data.total_ml,
            "last_drink_at": today_data.last_drink_at
        })

    def post(self, request):
        """
        Add a glass of water.
        Optional payload: {"amount_ml": 250} (defaults to 250)
        """
        user = request.user
        if user.role != 'USER':
             return Response({"error": "This feature is for Users only"}, status=403)

        amount_ml = request.data.get('amount_ml', 250)
        
        try:
            water_intake = WaterIntake.objects.get(user=user)
        except WaterIntake.DoesNotExist:
            water_intake = WaterIntake(user=user, records={})

        today_str = self.get_today_date_str()
        tz = pytz.timezone('Asia/Kolkata')
        current_time_str = datetime.now(tz).strftime('%H:%M')

        # Get or create today's record
        if today_str not in water_intake.records:
            water_intake.records[today_str] = DailyIntake(glasses=0, total_ml=0)
        
        daily_record = water_intake.records[today_str]
        daily_record.glasses += 1
        daily_record.total_ml += int(amount_ml)
        daily_record.last_drink_at = current_time_str
        
        water_intake.save()

        return Response({
            "message": "Water added!",
            "glasses": daily_record.glasses,
            "total_ml": daily_record.total_ml,
            "last_drink_at": daily_record.last_drink_at
        }, status=status.HTTP_200_OK)

class DailyPlanView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_today_date_str(self):
        # Default to India ID for now
        tz = pytz.timezone('Asia/Kolkata')
        return datetime.now(tz).strftime('%Y-%m-%d')
    
    def get(self, request):
        user = request.user
        today = self.get_today_date_str()
        
        # Try to find existing plan
        daily_plan = DailyPlan.objects.filter(user=user, date=today).first()
        
        if not daily_plan:
            # Generate new plan
            items, coach_msg = generate_daily_plan(user, today)
            daily_plan = DailyPlan(
                user=user,
                date=today,
                items=items,
                coach_message=coach_msg
            )
            daily_plan.save()
            
        serializer = DailyPlanSerializer(daily_plan)
        return Response(serializer.data)
    
    def patch(self, request):
        """
        Mark an item as completed or pending.
        Body: { "item_id": "uuid", "status": "completed" }
        """
        user = request.user
        today = self.get_today_date_str()
        item_id = request.data.get('item_id')
        new_status = request.data.get('status')
        
        daily_plan = DailyPlan.objects.filter(user=user, date=today).first()
        if not daily_plan:
            return Response({"error": "Plan not found"}, status=404)
            
        updated = False
        for item in daily_plan.items:
            if item.id == item_id:
                item.status = new_status
                updated = True
                break
        
        if updated:
            daily_plan.save()
            return Response({"message": "Status updated"})
            
        return Response({"error": "Item not found"}, status=404)
