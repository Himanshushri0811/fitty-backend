from datetime import datetime
from accounts.models import User, GymOwner
from gym_management.models import Member

def build_system_context(user):
    """
    Constructs the system prompt context based on user role and data.
    """
    base_context = f"""
    Current Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
    User Name: {user.name or user.username if hasattr(user, 'username') else 'User'}
    """
    
    if isinstance(user, GymOwner):
        return _build_gym_owner_context(user, base_context)
    elif isinstance(user, User):
        return _build_user_context(user, base_context)
    
    return base_context

def _build_gym_owner_context(owner, base_context):
    # Fetch Stats
    total_members = Member.objects(gym_owner=owner).count()
    
    # Active/Overdue logic (assuming 'PAID' is active, 'OVERDUE' is not)
    overdue_count = Member.objects(gym_owner=owner, fees_status='OVERDUE').count()
    
    today = datetime.utcnow().date()
    due_today_members = Member.objects(gym_owner=owner, fees_due_date=today)
    due_names = ", ".join([m.name for m in due_today_members]) or "None"
    
    context = f"""
    {base_context}
    ROLE: Gym Owner
    Gym Name: {owner.gym_name}
    Plan Type: {owner.plan_type}
    
    DATA SNAPSHOT:
    - Total Members: {total_members}
    - Members Overdue: {overdue_count}
    - Payments Due Today: {due_names}
    - Potential Profit (Est): {owner.current_profit}
    
    INSTRUCTIONS:
    - Assist with gym management questions.
    - If asked about specific members, use the list above (limited visibility).
    - Provide business insights if asked.
    - Be professional but motivating ("Chief", "Owner").
    """
    return context

def _build_user_context(user, base_context):
    goal = user.goal or "General Fitness"
    fitness_level = user.fitness_level or "Beginner"
    
    # Simple formatting of weekly plan
    plan_summary = "No active plan."
    if user.weekly_plan:
        plan_summary = ", ".join([d.day_name for d in user.weekly_plan])
        
    context = f"""
    {base_context}
    ROLE: Gym Member / Fitness Enthusiast
    Goal: {goal}
    Level: {fitness_level}
    Workout Days: {plan_summary}
    
    INSTRUCTIONS:
    - Act as a personal trainer and gym buddy.
    - If user asks for a workout, suggest based on '{goal}'.
    - Use terms like "Champ", "Buddy".
    - Keep answers concise and actionable.
    """
    return context
