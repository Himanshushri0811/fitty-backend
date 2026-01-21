from mongoengine import Document, StringField, DateTimeField, BooleanField, ReferenceField, DecimalField, DictField
from datetime import datetime
from accounts.models import GymOwner

class Subscription(Document):
    """
    Source of truth for SaaS billing and Plan Active state.
    """
    gym_owner = ReferenceField(GymOwner, required=True)
    plan_id = StringField(required=True, choices=('FREE', 'PRO_MONTHLY'))
    
    start_date = DateTimeField(default=datetime.utcnow)
    end_date = DateTimeField(required=True)
    
    razorpay_subscription_id = StringField()
    status = StringField(default='active', choices=('active', 'halted', 'completed', 'expired'))
    auto_renew = BooleanField(default=False)
    
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'subscriptions'}

class PaymentLog(Document):
    """
    Audit trail for every Razorpay interaction.
    """
    gym_owner = ReferenceField(GymOwner, required=True)
    transaction_id = StringField() # Internal ID
    razorpay_order_id = StringField()
    razorpay_payment_id = StringField()
    razorpay_signature = StringField()
    
    amount = DecimalField(precision=2)
    currency = StringField(default='INR')
    status = StringField(default='created') # created, success, failed
    
    payload_dump = DictField() # Store raw webhook/response data
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'payment_logs'}
