from datetime import datetime, timedelta
from .models import Subscription, PaymentLog
from accounts.models import GymOwner

class SubscriptionService:
    """
    Central logic for Plan Limitations and Enforcement.
    """

    PLANS = {
        'FREE': {
            'max_members': 50,
            'assistant_daily_limit': 20,
            'allow_export': False,
            'allow_branding': False
        },
        'PRO': { # Maps to PRO_MONTHLY
            'max_members': 999999,
            'assistant_daily_limit': 999999,
            'allow_export': True,
            'allow_branding': True
        }
    }

    @staticmethod
    def get_plan_limits(user):
        """
        Returns the limits dict for the user's current plan.
        """
        if not user or user.role != 'GYM_OWNER':
            return SubscriptionService.PLANS['FREE']
        
        # Check explicit plan_type
        # In a robust system, we would check the active Subscription document here.
        # For now, we trust the sync on GymOwner model but rely on this service to define the constants.
        plan = user.plan_type if user.plan_type in ['FREE', 'PRO'] else 'FREE'
        return SubscriptionService.PLANS[plan]

    @staticmethod
    def can_add_member(user):
        limits = SubscriptionService.get_plan_limits(user)
        return user.current_member_count < limits['max_members']

    @staticmethod
    def can_use_assistant(user):
        limits = SubscriptionService.get_plan_limits(user)
        
        # Reset Logic (Simple check)
        today = datetime.utcnow().date()
        if user.last_assistant_usage_date != today:
            user.assistant_daily_usage = 0
            user.last_assistant_usage_date = today
            user.save()
            
        return user.assistant_daily_usage < limits['assistant_daily_limit']

    @staticmethod
    def record_assistant_usage(user):
        user.assistant_daily_usage += 1
        user.save()

    @staticmethod
    def activate_pro_plan(user, duration_days=30):
        """
        Upgrades user to PRO and creates/updates Subscription.
        """
        now = datetime.utcnow()
        end_date = now + timedelta(days=duration_days)
        
        # Update User
        user.plan_type = 'PRO'
        user.is_pro_active = True
        user.plan_expiry = end_date
        user.max_members_limit = SubscriptionService.PLANS['PRO']['max_members']
        user.save()
        
        # Create Subscription Record
        Subscription(
            gym_owner=user,
            plan_id='PRO_MONTHLY',
            start_date=now,
            end_date=end_date,
            status='active',
            auto_renew=False
        ).save()
