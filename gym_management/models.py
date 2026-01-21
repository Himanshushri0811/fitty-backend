from mongoengine import Document, StringField, EmailField, DateTimeField, BooleanField, IntField, ReferenceField, DecimalField, DateField
from datetime import datetime
from accounts.models import GymOwner

class PaymentHistory(Document):
    """
    Immutable log of all payments in MongoDB
    """
    gym_owner = ReferenceField(GymOwner, reverse_delete_rule=4) # CASCADE
    order_id = StringField(required=True)
    payment_id = StringField()
    amount = DecimalField(precision=2)
    currency = StringField(default='INR')
    status = StringField(default='created') # created, success, failed
    plan_type = StringField()
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'payment_history'}

class Member(Document):
    """
    Gym Members in MongoDB
    """
    gym_owner = ReferenceField(GymOwner, reverse_delete_rule=4)
    name = StringField(required=True)
    mobile = StringField(required=True)
    email = StringField()
    gender = StringField(choices=('Male', 'Female', 'Other'))
    dob = DateField()
    
    # Membership Details
    join_date = DateField(default=datetime.utcnow().date)
    plan_name = StringField(default="Monthly") # e.g. "3 Months Strength"
    amount_paid = DecimalField(precision=2, default=0.0)
    
    fees_status = StringField(default='PENDING', choices=('PAID', 'PENDING', 'OVERDUE'))
    fees_due_date = DateField()
    notes = StringField()

    meta = {'collection': 'gym_members'}

    def __str__(self):
        return f"{self.name} ({self.gym_owner.gym_name if self.gym_owner else 'No Gym'})"
