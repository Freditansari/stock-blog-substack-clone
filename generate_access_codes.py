import random
import string
from flask import Flask
from app import app, db  # Import the existing Flask app instance
from models import AccessCode

# ✅ Ensure the app context is pushed
with app.app_context():

    def generate_access_code(length=10):
        """Generate a random 10-character access code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    # ✅ List of Default Expiration Days
    default_days_valid = [365, 180, 30]  # ⏳ 1 year, 6 months, 1 month

    # ✅ Generate & Insert Access Codes
    def create_default_access_codes():
        for days in default_days_valid:
            new_code = AccessCode(days_valid=days)

            # Prevent duplicate access codes
            if not AccessCode.query.filter_by(code=new_code.code).first():
                db.session.add(new_code)
                print(f"✅ Access Code '{new_code.code}' created for {days} days.")

        db.session.commit()
        print("✅ Default access codes added!")

    # ✅ Run the Function
    if __name__ == "__main__":
        create_default_access_codes()
