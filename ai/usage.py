from datetime import datetime
from accounts.models import User

# Dev Mode: 1000, Prod Free: 20
MAX_FREE_DAILY_MESSAGES = 1000 # Increased for Development as requested

def check_and_increment_quota(user):
    """
    Checks if user has sufficient quota.
    If yes, increments usage and returns True.
    If no, returns False.
    """
    today = datetime.utcnow().date()
    
    # Reset if new day
    if user.last_assistant_usage_date != today:
        user.assistant_daily_usage = 0
        user.last_assistant_usage_date = today
    
    # Check Limit
    limit_reached = False
    message = "Allowed"

    if user.role == 'GYM_OWNER':
        if user.plan_type == 'PRO':
            # Unlimited
            user.assistant_daily_usage += 1
            user.save()
            return True, "Allowed (Pro)"
        
        if user.assistant_daily_usage >= MAX_FREE_DAILY_MESSAGES:
            limit_reached = True
            message = "Daily limit reached. Upgrade to PRO for unlimited access."
            
    else: # Normal User
        if user.assistant_daily_usage >= MAX_FREE_DAILY_MESSAGES:
             limit_reached = True
             message = "Daily AI limit reached."

    if limit_reached:
        return False, message

    # Increment
    user.assistant_daily_usage += 1
    user.save()
    return True, message
