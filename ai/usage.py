from datetime import datetime
from accounts.models import User, GymOwner

MAX_FREE_DAILY_MESSAGES = 10

def check_and_increment_quota(user):
    """
    Checks if user (User or GymOwner) has sufficient quota.
    If yes, increments usage and returns True.
    If no, returns False.
    """
    today = datetime.utcnow().date()
    
    # Reset if new day
    if user.last_assistant_usage_date != today:
        user.assistant_daily_usage = 0
        user.last_assistant_usage_date = today
    
    # Check Limit
    # 1. Gym Owner Logic
    if isinstance(user, GymOwner):
        if user.plan_type == 'PRO':
            # Unlimited
            user.assistant_daily_usage += 1
            user.save()
            return True, "Allowed (Pro)"
        
        if user.assistant_daily_usage >= MAX_FREE_DAILY_MESSAGES:
            return False, "Daily limit reached. Upgrade to PRO for unlimited access."
            
    # 2. Regular User Logic
    elif isinstance(user, User):
        # Currently all users are 'free' effectively unless we have User tiers.
        # Let's assume a generous limit or distinct logic later.
        if user.assistant_daily_usage >= MAX_FREE_DAILY_MESSAGES:
             return False, "Daily AI limit reached."

    # Increment
    user.assistant_daily_usage += 1
    user.save()
    return True, "Allowed"
