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
    join_date = DateField(default=datetime.utcnow().date)
    fees_status = StringField(default='PENDING', choices=('PAID', 'PENDING'))
    fees_due_date = DateField()

    meta = {'collection': 'gym_members'}

    def __str__(self):
        return f"{self.name} ({self.gym_owner.gym_name if self.gym_owner else 'No Gym'})"
