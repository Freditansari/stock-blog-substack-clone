from app import app, db
from models import User, CreatorPayment
from datetime import datetime

# ✅ Ensure the app context is active
with app.app_context():
    creators = User.query.filter(User.premium_subscribers_count > 0).all()

    for creator in creators:
        monthly_earning = creator.premium_subscribers_count * 10  # Example: $10 per premium user

        # ✅ Avoid duplicate payments by checking if they were already paid this month
        last_payment = CreatorPayment.query.filter_by(creator_id=creator.id).order_by(CreatorPayment.payment_date.desc()).first()
        if last_payment and last_payment.payment_date.month == datetime.utcnow().month:
            print(f"❌ Skipping payment for {creator.username} (Already paid this month)")
            continue

        # ✅ Process payment (Integrate with PayPal, Stripe, etc. in a real system)
        print(f"✅ Paying ${monthly_earning} to {creator.username}")

        # ✅ Record the payment in the database
        new_payment = CreatorPayment(creator_id=creator.id, amount=monthly_earning)
        db.session.add(new_payment)
        db.session.commit()

    print("✅ All creator payments processed!")
